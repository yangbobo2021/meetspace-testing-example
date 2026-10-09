def enter(pid, r):
    number = r[8]
    args = r[:6]
    counters[f'syscall_{number}'] += 1
    record = {'number': number, 'args': args}
    if number in (64, 68):
        fd, addr, n = args[:3]
        if n > 16 * 1024 * 1024:
            uncovered.add('large_write_over_16MiB')
        else:
            record['write'] = (fd, read(pid, addr, n), 'pwrite64' if number == 68 else 'write')
    elif number == 66:
        fd, addr, n = args[:3]
        if n > 1024:
            uncovered.add('writev_over_1024_vectors')
        else:
            vectors = read(pid, addr, n * 16)
            parts = []
            for i in range(n):
                pointer = int.from_bytes(vectors[i * 16:i * 16 + 8], 'little')
                size = int.from_bytes(vectors[i * 16 + 8:i * 16 + 16], 'little')
                if size > 16 * 1024 * 1024:
                    uncovered.add('large_writev_over_16MiB')
                    continue
                parts.append(read(pid, pointer, size))
            record['write'] = (fd, b''.join(parts), 'writev')
    elif number in (63, 67, 65):
        if '/dev/random' in pathfd(pid, args[0]) or '/dev/urandom' in pathfd(pid, args[0]):
            if number in (63, 67):
                record['random_device'] = {'address': args[1], 'path': pathfd(pid, args[0])}
            else:
                uncovered.add('random_device_readv_not_controlled')
    elif number == 222:
        if args[2] & 2 and args[3] & 1 and (not args[3] & 32):
            record['mapping'] = {'length': args[1], 'fd': args[4], 'path': pathfd(pid, args[4])}
    elif number in (215, 227, 93, 94):
        for key, m in list(mappings.items()):
            owner, address = key
            if owner != group(pid):
                continue
            if number in (93, 94) or (args[0] < address + m['length'] and address < args[0] + args[1]):
                if m['length'] > 16 * 1024 * 1024:
                    uncovered.add('file_mmap_over_16MiB')
                else:
                    try:
                        content = read(pid, address, m['length'])
                        leaked = any((x and x in content for x in needles))
                        events.append({'kind': 'file_shared_mapping_scan', 'path': m['path'], 'bytes': m['length'], 'leak': leaked})
                        counters['scanned_shared_mappings'] += 1
                        if leaked:
                            counters['leaks'] += 1
                    except OSError as err:
                        failure = {'kind': 'mapping_read_failure', 'pid': pid, 'group': owner, 'path': m['path'], 'bytes': m['length'], 'syscall': number, 'errno': err.errno, 'reason': str(err), 'pending_unmapping_candidates': [{'pid': other, 'number': rec['number'], 'has_unmapping': bool(rec.get('unmapping'))} for other, rec in pending.items() if rec.get('unmapping')]}
                        candidate = None
                        if number in (93, 94):
                            for other, rec in pending.items():
                                if other == pid or rec['number'] != 215:
                                    continue
                                start = rec['args'][0]
                                end = start + (rec['args'][1] + 4095) // 4096 * 4096
                                if start <= address and end >= address + m['length'] and (key in rec.get('unmapping_scanned', set())) and any((old_key == key and old_mapping == m for old_key, old_mapping in rec.get('unmapping', []))):
                                    candidate = rec
                                    failure['pending_full_unmap_pid'] = other
                                    break
                        if candidate is None:
                            uncovered.add('mapping_unreadable_before_flush_or_exit')
                            events.append(failure)
                        else:
                            failure['kind'] = 'mapping_exit_scan_deferred_pending_full_unmap'
                            candidate.setdefault('dependent_exit_scans', []).append(failure)
                            events.append(failure)
                            counters['deferred_mapping_exit_scans'] += 1
                    else:
                        if number == 215:
                            record.setdefault('unmapping_scanned', set()).add(key)
                if number == 215:
                    record.setdefault('unmapping', []).append((key, dict(m)))
    elif number == 216 and (group(pid), args[0]) in mappings:
        record['remapping'] = dict(mappings[group(pid), args[0]])
    elif number in (35, 38, 276):
        record['outlet_event'] = 'unlink_or_rename'
    elif number in (206, 211):
        counters['network_send_calls'] += 1
    elif number in (425, 426, 427, 270, 69, 70, 71, 72, 76, 77, 285):
        uncovered.add(f'unhandled_IO_syscall_{number}')
    return record

if 'unmapping' in rec and ret == 0:
    start = rec['args'][0]
    end = start + (rec['args'][1] + 4095) // 4096 * 4096
    for key, m in rec['unmapping']:
        owner, address = key
        mappings.pop(key, None)
        old_end = address + m['length']
        if address < start:
            left = dict(m)
            left['length'] = start - address
            mappings[owner, address] = left
        if old_end > end:
            right = dict(m)
            right['length'] = old_end - end
            mappings[owner, end] = right
