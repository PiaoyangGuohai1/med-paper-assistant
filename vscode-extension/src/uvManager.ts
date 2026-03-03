/**
 * uv Manager — Auto-detection and installation of uv (Python package manager).
 *
 * Provides zero-config experience:
 * 1. Detect uv in PATH or known install locations
 * 2. Auto-install uv if not found (cross-platform)
 * 3. Derive uvx path from uv path
 *
 * With uv installed, `uvx med-paper-assistant` handles EVERYTHING:
 * - Python auto-download (if no Python on system)
 * - Package installation from PyPI in isolated environment
 * - All dependencies resolved automatically
 * - No interference with user's other packages
 */

import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * Get potential uv binary paths based on platform.
 * Covers PATH, common install locations, and platform-specific paths.
 */
export function getUvSearchPaths(): string[] {
    const homeDir = process.env.HOME || process.env.USERPROFILE || '';
    const platform = process.platform;

    if (platform === 'win32') {
        return [
            'uv',  // In PATH
            path.join(homeDir, 'AppData', 'Local', 'uv', 'bin', 'uv.exe'),
            path.join(homeDir, '.local', 'bin', 'uv.exe'),
            path.join(homeDir, '.cargo', 'bin', 'uv.exe'),
            'C:\\Program Files\\uv\\uv.exe',
        ];
    } else {
        return [
            'uv',  // In PATH
            path.join(homeDir, '.local', 'bin', 'uv'),
            path.join(homeDir, '.cargo', 'bin', 'uv'),
            '/usr/local/bin/uv',
            '/opt/homebrew/bin/uv',
        ];
    }
}

/**
 * Derive uvx path from a known uv path.
 * uvx is always in the same directory as uv.
 */
export function getUvxPath(uvPath: string): string {
    if (uvPath === 'uv') {
        return 'uvx';
    }
    const dir = path.dirname(uvPath);
    const ext = process.platform === 'win32' ? '.exe' : '';
    return path.join(dir, `uvx${ext}`);
}

/**
 * Get the install command for uv based on platform.
 */
export function getUvInstallCommand(): string {
    if (process.platform === 'win32') {
        return 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"';
    }
    return 'curl -LsSf https://astral.sh/uv/install.sh | sh';
}

/**
 * Find the actual uv binary path by checking known locations.
 * Returns the path string or null if not found.
 *
 * @param log - Optional logging function
 */
export async function findUvPath(log?: (msg: string) => void): Promise<string | null> {
    const paths = getUvSearchPaths();
    const _log = log || (() => {});

    for (const uvPath of paths) {
        try {
            if (uvPath === 'uv') {
                await execAsync('uv --version');
                _log('Found uv in PATH');
                return 'uv';
            } else if (fs.existsSync(uvPath)) {
                await execAsync(`"${uvPath}" --version`);
                _log(`Found uv at: ${uvPath}`);
                return uvPath;
            }
        } catch {
            // Continue to next path
        }
    }

    return null;
}

/**
 * Install uv and return the installed path.
 * This is the raw installer — callers should wrap with UI (progress notifications, etc.)
 *
 * @param log - Optional logging function
 * @returns The installed uv path, or null if installation failed
 */
export async function installUvHeadless(log?: (msg: string) => void): Promise<string | null> {
    const _log = log || (() => {});
    const command = getUvInstallCommand();

    _log(`Installing uv on ${process.platform}...`);
    _log(`Running: ${command}`);

    try {
        await execAsync(command, { timeout: 120000 });

        // Wait for filesystem to sync
        await new Promise(resolve => setTimeout(resolve, 1000));

        const uvPath = await findUvPath(log);
        if (uvPath) {
            _log(`uv installed successfully at: ${uvPath}`);
        } else {
            _log('uv installation completed but binary not found');
        }
        return uvPath;
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        _log(`uv installation failed: ${errorMsg}`);
        return null;
    }
}

/**
 * Build the MCP server command and args for marketplace mode.
 * Uses uvx for complete isolation — no PYTHONPATH needed.
 *
 * @param uvPath - Path to the uv binary
 * @param packageName - PyPI package name (e.g., 'med-paper-assistant')
 * @param pythonVersion - Optional Python version constraint (e.g., '>=3.11')
 * @returns [command, args] tuple
 */
export function buildUvxCommand(
    uvPath: string,
    packageName: string,
    pythonVersion?: string,
): [string, string[]] {
    const uvxPath = getUvxPath(uvPath);
    const args: string[] = [];

    if (pythonVersion) {
        args.push('--python', pythonVersion);
    }

    args.push(packageName);

    return [uvxPath, args];
}

/**
 * Build environment variables for MCP server child process.
 * Includes essential system variables for proper operation.
 *
 * @param options - Configuration options
 * @returns Environment variables object
 */
export function buildMcpEnv(options: {
    workspaceDir?: string;
    pythonPath?: string;
}): Record<string, string> {
    const env: Record<string, string> = {};

    // Workspace base directory for projects/logs
    if (options.workspaceDir) {
        env.MEDPAPER_BASE_DIR = options.workspaceDir;
    }

    // PYTHONPATH only for dev mode (bundled code)
    if (options.pythonPath) {
        env.PYTHONPATH = options.pythonPath;
    }

    // Inherit essential system variables
    if (process.env.PATH) { env.PATH = process.env.PATH; }
    if (process.env.HOME) { env.HOME = process.env.HOME; }
    if (process.env.SHELL) { env.SHELL = process.env.SHELL; }
    if (process.env.LANG) { env.LANG = process.env.LANG; }
    // Windows-specific
    if (process.env.USERPROFILE) { env.USERPROFILE = process.env.USERPROFILE; }
    if (process.env.APPDATA) { env.APPDATA = process.env.APPDATA; }
    if (process.env.LOCALAPPDATA) { env.LOCALAPPDATA = process.env.LOCALAPPDATA; }
    if (process.env.SYSTEMROOT) { env.SYSTEMROOT = process.env.SYSTEMROOT; }
    if (process.env.COMSPEC) { env.COMSPEC = process.env.COMSPEC; }
    // Windows: inherit TEMP/TMP for uv cache
    if (process.env.TEMP) { env.TEMP = process.env.TEMP; }
    if (process.env.TMP) { env.TMP = process.env.TMP; }

    return env;
}
