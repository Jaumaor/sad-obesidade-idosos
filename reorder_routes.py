#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reordenar rotas no arquivo de namespace de pacientes"""

# Read the file
with open('src/backend/api/docs/namespaces/pacientes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and reorder: move the @ns.route('/pacientes/<paciente_id>') section to before 'return ns'
lines = content.split('\n')

# Find line indices
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '@ns.route("/pacientes/<paciente_id>")' in line:
        start_idx = i
        print(f"[INFO] Found @ns.route() at line {i}")
    if start_idx is not None and 'class PacienteDetalheResource' in line:
        print(f"[INFO] Found class at line {i}")
        # Find the end of this class (next @ns.route or return ns)
        for j in range(i+1, len(lines)):
            if lines[j].strip().startswith('@ns.route') or lines[j].strip() == 'return ns':
                end_idx = j
                print(f"[INFO] Found end at line {j}")
                break

if start_idx is not None and end_idx is not None:
    # Extract the block
    block = lines[start_idx:end_idx]
    print(f"[INFO] Extracted {len(block)} lines")
    
    # Remove from original position
    lines = lines[:start_idx] + lines[end_idx:]
    
    # Find 'return ns' position
    for i, line in enumerate(lines):
        if line.strip() == 'return ns':
            print(f"[INFO] Found 'return ns' at line {i}, inserting block")
            # Insert before 'return ns'
            lines = lines[:i] + block + [''] + lines[i:]
            break
    
    # Write back
    with open('src/backend/api/docs/namespaces/pacientes.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('[OK] Arquivo reordenado com sucesso')
else:
    print(f'[ERRO] start_idx={start_idx}, end_idx={end_idx}')
