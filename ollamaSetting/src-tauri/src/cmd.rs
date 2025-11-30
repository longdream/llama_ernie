use std::process::{Command, Output, Stdio};
use std::io::Result;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

/// Create a Command that hides the console window on Windows
pub fn hidden_command(program: &str) -> Command {
    let mut cmd = Command::new(program);
    
    #[cfg(windows)]
    cmd.creation_flags(CREATE_NO_WINDOW);
    
    cmd.stdin(Stdio::null())
       .stdout(Stdio::piped())
       .stderr(Stdio::piped());
    
    cmd
}

/// Run a hidden PowerShell command
pub fn powershell(args: &[&str]) -> Result<Output> {
    hidden_command("powershell")
        .args(args)
        .output()
}

/// Run a hidden command with arguments
pub fn run(program: &str, args: &[&str]) -> Result<Output> {
    hidden_command(program)
        .args(args)
        .output()
}

