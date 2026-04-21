//! bench-rs — analyze results.tsv and emit a markdown summary.
//!
//! Mirrors the interface of `bench.py` (summary / latest / best) so
//! the two implementations can be cross-checked against the same log.

use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};
use serde::Deserialize;

#[derive(Parser)]
#[command(name = "bench-rs", about = "Analyze results.tsv from the CLI.", version)]
struct Cli {
    /// Path to results.tsv.
    #[arg(long, default_value = "results.tsv")]
    results: PathBuf,

    #[command(subcommand)]
    command: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Full markdown summary of all runs.
    Summary,
    /// Most recent run, diffed against the baseline.
    Latest,
    /// The single best run by lowest val_bpb.
    Best,
}

#[derive(Debug, Deserialize, Clone)]
struct Row {
    commit: String,
    val_bpb: f64,
    #[allow(dead_code)]
    memory_gb: f64,
    status: String,
    description: String,
}

fn load(path: &PathBuf) -> Result<Vec<Row>, Box<dyn std::error::Error>> {
    let mut reader = csv::ReaderBuilder::new()
        .delimiter(b'\t')
        .has_headers(true)
        .from_path(path)?;
    let rows: Result<Vec<Row>, _> = reader.deserialize().collect();
    Ok(rows?)
}

fn best(rows: &[Row]) -> &Row {
    rows.iter()
        .min_by(|a, b| a.val_bpb.partial_cmp(&b.val_bpb).expect("val_bpb is finite"))
        .expect("caller guarantees at least one row")
}

fn improvement_pct(baseline: f64, new: f64) -> f64 {
    100.0 * (baseline - new) / baseline
}

fn cmd_summary(rows: &[Row]) {
    let baseline = &rows[0];
    let b = best(rows);
    let kept = rows.iter().filter(|r| r.status == "keep").count();
    let discarded = rows.iter().filter(|r| r.status == "discard").count();
    let delta = improvement_pct(baseline.val_bpb, b.val_bpb);

    println!("# autoresearch-mlx — experiment summary\n");
    println!(
        "- Runs logged: **{}** (kept: {}, discarded: {})",
        rows.len(),
        kept,
        discarded
    );
    println!(
        "- Baseline: `{}` · val_bpb `{:.6}`",
        baseline.commit, baseline.val_bpb
    );
    println!("- Best:     `{}` · val_bpb `{:.6}`", b.commit, b.val_bpb);
    println!("- Improvement over baseline: **{:.2}%**\n", delta);

    println!("## All runs\n");
    println!("| Commit | val_bpb | Status | Description |");
    println!("|---|---:|---|---|");
    for r in rows {
        println!(
            "| `{}` | {:.6} | {} | {} |",
            r.commit, r.val_bpb, r.status, r.description
        );
    }
}

fn cmd_latest(rows: &[Row]) {
    let last = rows.last().expect("at least one row");
    let first = &rows[0];
    let delta = improvement_pct(first.val_bpb, last.val_bpb);
    println!(
        "Latest: `{}`  val_bpb {:.6}  ({})",
        last.commit, last.val_bpb, last.status
    );
    println!(
        "  vs baseline `{}` ({:.6}): {:+.2}%",
        first.commit, first.val_bpb, delta
    );
    println!("  note: {}", last.description);
}

fn cmd_best(rows: &[Row]) {
    let b = best(rows);
    println!(
        "Best: `{}`  val_bpb {:.6}  ({})",
        b.commit, b.val_bpb, b.status
    );
    println!("  note: {}", b.description);
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let rows = match load(&cli.results) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("bench-rs: failed to load {}: {}", cli.results.display(), e);
            return ExitCode::FAILURE;
        }
    };
    if rows.is_empty() {
        eprintln!("bench-rs: {} has no rows", cli.results.display());
        return ExitCode::FAILURE;
    }
    match cli.command {
        Cmd::Summary => cmd_summary(&rows),
        Cmd::Latest => cmd_latest(&rows),
        Cmd::Best => cmd_best(&rows),
    }
    ExitCode::SUCCESS
}
