import datetime
import re
from storage.db import hash_password

def _list_tables(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return [r[0] for r in cur.fetchall()]
    except Exception:
        # PostgreSQL / MySQL fallback
        try:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            return [r[0] for r in cur.fetchall()]
        except Exception:
            return []

def _get_table_columns(conn, table):
    """
    Returns list of dicts with keys: name, type, notnull (0/1), dflt_value, pk (0/1).
    SQLite PRAGMA compatible format.
    """
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table})")
        cols = []
        for r in cur.fetchall():
            cols.append({"name": r[1], "type": (r[2] or "").upper(), "notnull": r[3], "dflt_value": r[4], "pk": r[5]})
        return cols
    except Exception:
        # Try information_schema fallback
        try:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = ?
                """, (table,)
            )
            cols = []
            for r in cur.fetchall():
                cols.append({
                    "name": r[0],
                    "type": (r[1] or "").upper(),
                    "notnull": 0 if (r[2] or "").upper().startswith("YES") else 1,
                    "dflt_value": r[3],
                    "pk": 0,
                })
            return cols
        except Exception:
            return []

def _get_foreign_keys(conn, table):
    """
    Return dict mapping from column -> (ref_table, ref_column)
    SQLite PRAGMA format -> rows: id, seq, table, from, to, ...
    """
    cur = conn.cursor()
    fk_map = {}
    try:
        cur.execute(f"PRAGMA foreign_key_list({table})")
        for r in cur.fetchall():
            # r[2] -> referenced table, r[3] -> from column, r[4] -> to column
            fk_map[r[3]] = (r[2], r[4])
    except Exception:
        # fallback: not available, return empty
        pass
    return fk_map

def _sample_value_for_column(table, col, fk_map, created_rows):
    name = col["name"].lower()
    ctype = (col.get("type") or "").upper()
    # Primary key autoinc: skip (None)
    if col.get("pk"):
        return None
    # Foreign key
    if name in fk_map:
        ref_table, ref_col = fk_map[name]
        ref_id = created_rows.get(ref_table)
        if ref_id is None:
            # ensure referenced table has a row
            ref_id = _create_sample_row(conn=_global_conn, table=ref_table, created_rows=created_rows, in_progress=set())
        return ref_id
    # Default/dflt_value provided
    if col.get("dflt_value") is not None:
        return col.get("dflt_value")
    # Heuristics by column name
    if "email" in name:
        return f"{table}_{name}@example.com"
    if "password" in name:
        return hash_password("password123")
    if "phone" in name or "contact" in name:
        return "09123456789"
    if "price" in name or "amount" in name or "cost" in name or "salary" in name:
        return 1000
    if "date" in name or "time" in name or "created_at" in name or "updated_at" in name:
        return datetime.datetime.utcnow().isoformat(sep=" ")
    if "is_" in name or name.startswith("has_"):
        return 1
    # Based on SQL type
    if "CHAR" in ctype or "TEXT" in ctype or "CLOB" in ctype:
        return f"seed_{table}_{name}"
    if "INT" in ctype or "TINYINT" in ctype:
        return 1
    if "REAL" in ctype or "FLOA" in ctype or "DOUB" in ctype or "DEC" in ctype:
        return 1.0
    # Fallback string
    return f"seed_{table}_{name}"

def _create_sample_row(conn, table, created_rows, in_progress):
    # Avoid recursion loops
    if table in created_rows:
        return created_rows[table]
    if table in in_progress:
        return None
    in_progress.add(table)
    cur = conn.cursor()
    # Skip if table already has data
    try:
        cur.execute(f"SELECT COUNT(*) as c FROM \"{table}\"")
        if cur.fetchone()[0] > 0:
            # Get an existing id if possible
            try:
                cur.execute(f"SELECT id FROM \"{table}\" LIMIT 1")
                row = cur.fetchone()
                if row:
                    created_rows[table] = row[0]
                    in_progress.remove(table)
                    return created_rows[table]
            except Exception:
                in_progress.remove(table)
                return None
    except Exception:
        # ignore
        pass
    cols = _get_table_columns(conn, table)
    fk_map = _get_foreign_keys(conn, table)
    data = {}
    for c in cols:
        val = _sample_value_for_column(table, c, fk_map, created_rows)
        # Skip primary key if None
        if val is None:
            continue
        data[c["name"]] = val
    if not data:
        in_progress.remove(table)
        return None
    # Build SQL insert
    col_names = list(data.keys())
    placeholders = ", ".join(["?"] * len(col_names))
    col_list = ", ".join([f'"{c}"' for c in col_names])
    vals = [data[c] for c in col_names]
    try:
        cur.execute(f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})', vals)
        conn.commit()
        inserted_id = None
        try:
            inserted_id = cur.lastrowid
        except Exception:
            pass
        # Try to fetch id column if lastrowid not available
        if not inserted_id:
            try:
                cur.execute(f"SELECT id FROM \"{table}\" ORDER BY rowid DESC LIMIT 1")
                r = cur.fetchone()
                if r:
                    inserted_id = r[0]
            except Exception:
                inserted_id = None
        created_rows[table] = inserted_id
        print(f"[seed] Inserted into {table}: {data}")
    except Exception as ex:
        # Could fail due to constraints; ignore
        print(f"[seed] Failed to insert into {table}: {ex}")
    in_progress.remove(table)
    return created_rows.get(table)

def seed_all_tables(conn):
    """
    Iterate every table in DB and ensure one sample row is present
    for every table and every column (where possible).
    """
    global _global_conn
    _global_conn = conn  # helper for recursive FK creation
    tables = _list_tables(conn)
    created_rows = {}
    for t in tables:
        # skip sqlite metadata
        if t.startswith("sqlite_"):
            continue
        # skip if table has data already
        cur = conn.cursor()
        try:
            cur.execute(f'SELECT COUNT(*) as c FROM "{t}"')
            if cur.fetchone()[0] > 0:
                continue
        except Exception:
            # fallback: try selecting * and limit 1
            try:
                cur.execute(f'SELECT 1 FROM "{t}" LIMIT 1')
                if cur.fetchone():
                    continue
            except Exception:
                pass
        _create_sample_row(conn, t, created_rows, set())

    # Add richer demo content for UI testing (idempotent)
    try:
        _seed_demo_data(conn)
    except Exception as ex:
        print(f"[seed] demo seeding failed: {ex}")


def _seed_demo_data(conn):
    """Insert demo users, listings, images, reservations, activity logs, reports, and payments."""
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    # Ensure a variety of users: admins, PMs, tenants
    base_users = [
        ("admin@example.com", "admin123", "admin", "Super Admin"),
    ]

    # Add multiple PMs and tenants
    for i in range(1, 7):
        base_users.append((f"pm{i}@example.com", "password123", "pm", f"PM {i}"))
    for i in range(1, 9):
        base_users.append((f"tenant{i}@example.com", "password123", "tenant", f"Tenant {i}"))

    # Insert users idempotently
    for email, plain_pw, role, full_name in base_users:
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if not cur.fetchone():
            hashed = hash_password(plain_pw)
            cur.execute(
                "INSERT INTO users (email, password, role, full_name, created_at) VALUES (?, ?, ?, ?, ?)",
                (email, hashed, role, full_name, now)
            )

    conn.commit()

    # Ensure user_settings and addresses for each user
    cur.execute("SELECT id FROM users")
    all_users = [r[0] for r in cur.fetchall()]
    for uid in all_users:
        # settings
        cur.execute("SELECT setting_id FROM user_settings WHERE user_id = ?", (uid,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO user_settings (user_id, popup_notifications, chat_notifications, email_notifications, reservation_confirmation_notif, cancellation_notif, payment_update_notif, rent_reminders_notif, created_at, updated_at) VALUES (?, 1,1,1,1,1,1,1, ?, ?)",
                (uid, now, now)
            )
        # address
        cur.execute("SELECT address_id FROM user_addresses WHERE user_id = ? AND is_primary = 1", (uid,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO user_addresses (user_id, house_no, street, barangay, city, province, postal_code, is_primary, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (uid, f"{100+uid}", f"Demo Street {uid}", "Demo Brgy", "Demo City", "Demo Province", f"{4000+uid}", now, now)
            )

    conn.commit()

    # Create listings: 2-3 listings per PM
    cur.execute("SELECT id FROM users WHERE role = 'pm'")
    pm_ids = [r[0] for r in cur.fetchall()]
    listing_ids = []
    for pm in pm_ids:
        for j in range(1, 4):
            address = f"{j} - {pm} Demo Boarding House, Near Campus"
            cur.execute("SELECT id FROM listings WHERE pm_id = ? AND address = ?", (pm, address))
            if cur.fetchone():
                continue
            price = 2000 + (pm % 5) * 500 + j * 250
            desc = f"Comfortable room number {j} offered by PM {pm}"
            lodging = "Single room; WiFi; Shared kitchen"
            cur.execute("INSERT INTO listings (pm_id, address, price, description, lodging_details, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'approved', ?, ?)", (pm, address, price, desc, lodging, now, now))
            lid = cur.lastrowid
            listing_ids.append(lid)
            # Add 2 images per listing idempotently
            for img_i in range(1, 3):
                img_path = f"assets/listing_{lid}_{img_i}.jpg"
                cur.execute("SELECT id FROM listing_images WHERE listing_id = ? AND image_path = ?", (lid, img_path))
                if not cur.fetchone():
                    cur.execute("INSERT INTO listing_images (listing_id, image_path) VALUES (?, ?)", (lid, img_path))

    conn.commit()

    # Create reservations: assign tenants to listings
    cur.execute("SELECT id FROM users WHERE role = 'tenant'")
    tenant_ids = [r[0] for r in cur.fetchall()]
    now_dt = datetime.datetime.utcnow()
    for idx, lid in enumerate(listing_ids):
        t = tenant_ids[idx % len(tenant_ids)] if tenant_ids else None
        if not t:
            break
        # future reservation
        start_date = (now_dt + datetime.timedelta(days=idx % 10 + 1)).date().isoformat()
        end_date = (now_dt + datetime.timedelta(days=idx % 10 + 7)).date().isoformat()
        cur.execute("SELECT id FROM reservations WHERE listing_id = ? AND tenant_id = ? AND start_date = ?", (lid, t, start_date))
        if not cur.fetchone():
            cur.execute("INSERT INTO reservations (listing_id, tenant_id, start_date, end_date, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)", (lid, t, start_date, end_date, now))
        # add a few past reservations for charting
        for m in range(1, 5):
            past_start = (now_dt - datetime.timedelta(days=30 * m + idx)).date().isoformat()
            past_end = (now_dt - datetime.timedelta(days=30 * m - 5)).date().isoformat()
            tenant_for_past = tenant_ids[(idx + m) % max(1, len(tenant_ids))] if tenant_ids else None
            cur.execute("INSERT OR IGNORE INTO reservations (listing_id, tenant_id, start_date, end_date, status, created_at) VALUES (?, ?, ?, ?, 'approved', ?)", (lid, tenant_for_past, past_start, past_end, (now_dt - datetime.timedelta(days=30 * m)).isoformat()))

    conn.commit()

    # Saved listings: have tenants save several listings
    for t in tenant_ids:
        # save up to 5 listings
        if listing_ids:
            start_idx = t % max(1, len(listing_ids))
            for lid in listing_ids[start_idx:start_idx + 5]:
                cur.execute("SELECT saved_id FROM saved_listings WHERE user_id = ? AND listing_id = ?", (t, lid))
                if not cur.fetchone():
                    cur.execute("INSERT INTO saved_listings (user_id, listing_id, saved_at) VALUES (?, ?, ?)", (t, lid, now))

    conn.commit()

    # Notifications: add a few per user
    notif_types = ["view", "save", "reservation", "reminder", "payment"]
    for uid in all_users[:20]:
        for n in range(3):
            ntype = notif_types[(uid + n) % max(1, len(notif_types))]
            msg = f"Demo {ntype} notification #{n+1} for user {uid}"
            cur.execute("INSERT INTO notifications (user_id, notification_type, category, message, is_read, created_at) VALUES (?, ?, 'activity', ?, 0, ?)", (uid, ntype, msg, now))

    conn.commit()

    # Payment transactions for some reservations
    cur.execute("SELECT id, listing_id, tenant_id FROM reservations LIMIT 20")
    res_rows = cur.fetchall()
    for r in res_rows:
        res_id = r[0]
        user_id = r[2]
        # if a payment doesn't exist for this reservation, create one
        cur.execute("SELECT transaction_id FROM payment_transactions WHERE reservation_id = ?", (res_id,))
        if not cur.fetchone():
            amt = 1000 + (res_id % 5) * 250
            cur.execute("INSERT INTO payment_transactions (reservation_id, user_id, amount, payment_method, transaction_reference, status, payment_date, created_at) VALUES (?, ?, ?, ?, ?, 'Completed', ?, ?)", (res_id, user_id, amt, 'GCash', f'TXN{res_id:05d}', now, now))

    conn.commit()

    # Reviews: add multiple reviews per listing
    for lid in listing_ids[:20]:
        for r_i in range(1, 6):
            reviewer = tenant_ids[(lid + r_i) % max(1, len(tenant_ids))] if tenant_ids else None
            if not reviewer:
                continue
            # avoid duplicate identical review
            comment = f"Sample review {r_i} for listing {lid}"
            cur.execute("SELECT review_id FROM reviews WHERE listing_id = ? AND user_id = ? AND comment = ?", (lid, reviewer, comment))
            if not cur.fetchone():
                rating = (r_i % 5) + 1
                cur.execute("INSERT INTO reviews (listing_id, user_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)", (lid, reviewer, rating, comment, now))

    conn.commit()

    # Messages: create simple chat threads between tenants and PMs
    for idx, t in enumerate(tenant_ids[:10]):
        pm = pm_ids[idx % len(pm_ids)] if pm_ids else None
        if not pm:
            break
        for m in range(1, 6):
            content = f"Message {m} from tenant {t} to pm {pm}"
            cur.execute("INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at) VALUES (?, ?, ?, 0, ?)", (t, pm, content, now))
            # a reply
            cur.execute("INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at) VALUES (?, ?, ?, 0, ?)", (pm, t, f'Reply {m} to tenant {t}', now))

    conn.commit()

    # -------------------------------------------------
    # Ensure minimum counts (idempotent) across tables
    # Add additional rows so UI has richer data (5-10 extras per table)
    # -------------------------------------------------
    def _ensure_min_rows(table, desired, create_func):
        cur.execute(f'SELECT COUNT(*) as c FROM "{table}"')
        cur_count = cur.fetchone()[0]
        to_add = max(0, desired - cur_count)
        for _ in range(to_add):
            try:
                create_func()
            except Exception as e:
                print(f"[seed] failed to create extra row for {table}: {e}")

    # small helpers to create rows
    def _create_extra_user(i):
        email = f"extra_user_{i}@example.com"
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            return
        hashed = hash_password("Password1!")
        role = "tenant" if i % 2 == 0 else "pm"
        full_name = f"Extra {role.title()} {i}"
        cur.execute("INSERT INTO users (email, password, role, full_name, created_at) VALUES (?, ?, ?, ?, ?)", (email, hashed, role, full_name, now))

    def _create_extra_listing(i):
        # pick a random pm
        cur.execute("SELECT id FROM users WHERE role = 'pm' ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(pm_ids)),))
        row = cur.fetchone()
        pm = row[0] if row else (pm_ids[0] if pm_ids else 1)
        address = f"Extra Listing {i} by PM {pm}, Demo Address"
        cur.execute("SELECT id FROM listings WHERE pm_id = ? AND address = ?", (pm, address))
        if cur.fetchone():
            return
        price = 2500 + (i % 6) * 300
        desc = f"Extra demo listing {i}"
        cur.execute("INSERT INTO listings (pm_id, address, price, description, lodging_details, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'approved', ?, ?)", (pm, address, price, desc, "Single; WiFi", now, now))
        lid = cur.lastrowid
        # two images
        for img_i in range(2):
            img_path = f"assets/extra_listing_{lid}_{img_i}.jpg"
            cur.execute("INSERT OR IGNORE INTO listing_images (listing_id, image_path) VALUES (?, ?)", (lid, img_path))

    def _create_extra_reservation(i):
        # pick a listing and tenant
        cur.execute("SELECT id FROM listings ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(listing_ids)),))
        lr = cur.fetchone()
        if not lr:
            return
        lid = lr[0]
        cur.execute("SELECT id FROM users WHERE role = 'tenant' ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(tenant_ids)),))
        tr = cur.fetchone()
        if not tr:
            return
        tid = tr[0]
        start = (datetime.datetime.utcnow() + datetime.timedelta(days=2 + i)).date().isoformat()
        end = (datetime.datetime.utcnow() + datetime.timedelta(days=5 + i)).date().isoformat()
        cur.execute("INSERT OR IGNORE INTO reservations (listing_id, tenant_id, start_date, end_date, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)", (lid, tid, start, end, now))

    def _create_extra_saved(i):
        cur.execute("SELECT id FROM users WHERE role = 'tenant' ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(tenant_ids)),))
        ur = cur.fetchone()
        cur.execute("SELECT id FROM listings ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(listing_ids)),))
        lr = cur.fetchone()
        if not ur or not lr:
            return
        cur.execute("INSERT OR IGNORE INTO saved_listings (user_id, listing_id, saved_at) VALUES (?, ?, ?)", (ur[0], lr[0], now))

    def _create_extra_notification(i):
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(all_users)),))
        ur = cur.fetchone()
        if not ur:
            return
        msg = f"Extra notification {i}"
        ntype = notif_types[i % len(notif_types)]
        cur.execute("INSERT INTO notifications (user_id, notification_type, category, message, is_read, created_at) VALUES (?, ?, 'activity', ?, 0, ?)", (ur[0], ntype, msg, now))

    def _create_extra_payment(i):
        # tie to an existing reservation if exist
        cur.execute("SELECT id FROM reservations ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(res_rows)),))
        rr = cur.fetchone()
        if not rr:
            return
        res_id = rr[0]
        cur.execute("SELECT transaction_id FROM payment_transactions WHERE reservation_id = ?", (res_id,))
        if cur.fetchone():
            return
        amt = 1200 + (i % 6) * 200
        cur.execute("INSERT INTO payment_transactions (reservation_id, user_id, amount, payment_method, transaction_reference, status, payment_date, created_at) VALUES (?, ?, ?, ?, ?, 'Completed', ?, ?)", (res_id, tenant_ids[0] if tenant_ids else 1, amt, 'GCash', f'EXTTXN{i:05d}', now, now))

    def _create_extra_review(i):
        cur.execute("SELECT id FROM listings ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(listing_ids)),))
        lr = cur.fetchone()
        cur.execute("SELECT id FROM users WHERE role = 'tenant' ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(tenant_ids)),))
        ur = cur.fetchone()
        if not lr or not ur:
            return
        comment = f"Extra seeded review {i}"
        cur.execute("INSERT OR IGNORE INTO reviews (listing_id, user_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)", (lr[0], ur[0], (i % 5) + 1, comment, now))

    def _create_extra_message(i):
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(all_users)),))
        a = cur.fetchone()
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1 OFFSET ?", ((i+1) % max(1, len(all_users)),))
        b = cur.fetchone()
        if not a or not b:
            return
        cur.execute("INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at) VALUES (?, ?, ?, 0, ?)", (a[0], b[0], f'Auto message {i}', now))

    def _create_extra_report(i):
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(all_users)),))
        ur = cur.fetchone()
        cur.execute("SELECT id FROM listings ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(listing_ids)),))
        lr = cur.fetchone()
        if not ur:
            return
        cur.execute("INSERT INTO reports (user_id, listing_id, message, status, created_at) VALUES (?, ?, ?, 'open', ?)", (ur[0], lr[0] if lr else None, f'Auto report {i}', now))

    def _create_extra_activity(i):
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(all_users)),))
        ur = cur.fetchone()
        cur.execute("INSERT INTO activity_logs (user_id, action, details, created_at) VALUES (?, ?, ?, ?)", (ur[0] if ur else None, f'AutoAction{i}', f'AutoDetails{i}', now))

    def _create_extra_token(i):
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1 OFFSET ?", (i % max(1, len(all_users)),))
        ur = cur.fetchone()
        if not ur:
            return
        token = f'token_extra_{i}_{ur[0]}'
        expires = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
        cur.execute("INSERT OR IGNORE INTO password_reset_tokens (user_id, token, expires_at, used, created_at) VALUES (?, ?, ?, 0, ?)", (ur[0], token, expires, now))

    # Desired minimums
    desired = {
        'users': 20,
        'listings': 30,
        'listing_images': 50,
        'reservations': 40,
        'saved_listings': 50,
        'notifications': 50,
        'payment_transactions': 30,
        'reviews': 60,
        'messages': 80,
        'reports': 10,
        'activity_logs': 40,
        'password_reset_tokens': 10,
    }

    # Run ensures
    for i in range(1, 21):
        _create_extra_user(i)
    conn.commit()

    # refresh helper lists
    cur.execute("SELECT id FROM users WHERE role = 'pm'")
    pm_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users WHERE role = 'tenant'")
    tenant_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM listings")
    listing_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users")
    all_users = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM reservations")
    res_rows = [r[0] for r in cur.fetchall()]

    for i in range(1, 31):
        _create_extra_listing(i)
    conn.commit()

    for i in range(1, 41):
        _create_extra_reservation(i)
    conn.commit()

    for i in range(1, 51):
        _create_extra_saved(i)
        _create_extra_notification(i)
        _create_extra_message(i)
        _create_extra_review(i)
        _create_extra_payment(i)
        _create_extra_report(i)
        _create_extra_activity(i)
        _create_extra_token(i)
    conn.commit()
