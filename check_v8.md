python3 -c "
import json, os

# V8 config check
from loopagi.arc.solve_improved import ImprovedSolverConfig
c = ImprovedSolverConfig()
print('=== V8 Config ===')
print(f'  multi_strategy={c.enable_multi_strategy}, diff_refine={c.enable_diff_refine}, diff_thresh={c.diff_refine_threshold}')
print(f'  ttt={c.enable_ttt}, ttt_timeout=900, adaptive_steps=True')

# Module check
from loopagi.arc.pass_at_k import multi_strategy_vote
from loopagi.arc.diff_refiner import refine_with_diff
from loopagi.arc.ttt import TTTConfig
tc = TTTConfig()
print(f'  ttt_timeout={tc.timeout}, ttt_adaptive={tc.adaptive_steps}')
print('  All V8 modules import OK')

# Test count
import subprocess
r = subprocess.run(['uv', 'run', 'pytest', 'tests/', '-q', '--tb=no'], capture_output=True, text=True, cwd='/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code')
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

# Git status
r2 = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True, cwd='/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code')
print('\n=== Git ===')
print(f'  Branch: feature/arc-improvements-v3')
for line in r2.stdout.strip().split('\n'):
    print(f'  {line}')

# New files
print('\n=== V8 New Files ===')
for f in ['loopagi/arc/pass_at_k.py', 'loopagi/arc/diff_refiner.py']:
    p = f'/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code/{f}'
    lines = sum(1 for _ in open(p))
    print(f'  {f}: {lines} lines')
" 2>/dev/null

py -c "
import json, os

# V8 config check
from loopagi.arc.solve_improved import ImprovedSolverConfig
c = ImprovedSolverConfig()
print('=== V8 Config ===')
print(f'  multi_strategy={c.enable_multi_strategy}, diff_refine={c.enable_diff_refine}, diff_thresh={c.diff_refine_threshold}')
print(f'  ttt={c.enable_ttt}, ttt_timeout=900, adaptive_steps=True')

# Module check
from loopagi.arc.pass_at_k import multi_strategy_vote
from loopagi.arc.diff_refiner import refine_with_diff
from loopagi.arc.ttt import TTTConfig
tc = TTTConfig()
print(f'  ttt_timeout={tc.timeout}, ttt_adaptive={tc.adaptive_steps}')
print('  All V8 modules import OK')

# Test count
import subprocess
r = subprocess.run(['uv', 'run', 'pytest', 'tests/', '-q', '--tb=no'], capture_output=True, text=True, cwd='/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code')
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

# Git status
r2 = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True, cwd='/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code')
print('\n=== Git ===')
print(f'  Branch: feature/arc-improvements-v3')
for line in r2.stdout.strip().split('\n'):
    print(f'  {line}')

# New files
print('\n=== V8 New Files ===')
for f in ['loopagi/arc/pass_at_k.py', 'loopagi/arc/diff_refiner.py']:
    p = f'/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code/{f}'
    lines = sum(1 for _ in open(p))
    print(f'  {f}: {lines} lines')
" 2>/dev/null


py -c "
import json, os

# V8 config check
from loopagi.arc.solve_improved import ImprovedSolverConfig
c = ImprovedSolverConfig()
print('=== V8 Config ===')
print(f'  multi_strategy={c.enable_multi_strategy}, diff_refine={c.enable_diff_refine}, diff_thresh={c.diff_refine_threshold}')
print(f'  ttt={c.enable_ttt}, ttt_timeout=900, adaptive_steps=True')

# Module check
from loopagi.arc.pass_at_k import multi_strategy_vote
from loopagi.arc.diff_refiner import refine_with_diff
from loopagi.arc.ttt import TTTConfig
tc = TTTConfig()
print(f'  ttt_timeout={tc.timeout}, ttt_adaptive={tc.adaptive_steps}')
print('  All V8 modules import OK')

# Test count
import subprocess
r = subprocess.run(['uv', 'run', 'pytest', 'tests/', '-q', '--tb=no'], capture_output=True, text=True, cwd='/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code')
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

# Git status
r2 = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True, cwd='/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code')
print('\n=== Git ===')
print(f'  Branch: feature/arc-improvements-v3')
for line in r2.stdout.strip().split('\n'):
    print(f'  {line}')

# New files
print('\n=== V8 New Files ===')
for f in ['loopagi/arc/pass_at_k.py', 'loopagi/arc/diff_refiner.py']:
    p = f'/home/anubix/Documents/CODE/BOOKS/god-in-the-loop-code/{f}'
    lines = sum(1 for _ in open(p))
    print(f'  {f}: {lines} lines')
" 2>/dev/null

