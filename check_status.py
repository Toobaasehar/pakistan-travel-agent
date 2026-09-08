import sqlite3

conn = sqlite3.connect('travel.db')
cur = conn.cursor()

# Show all image records
cur.execute("""
    SELECT d.id, d.name, di.image_url, di.source
    FROM destinations d 
    JOIN destination_images di ON d.id = di.destination_id
    ORDER BY d.id
""")
rows = cur.fetchall()
print(f'Total records with images: {len(rows)}')
print()

real = 0
placeholder = 0
empty = 0
for r in rows:
    url = r[2] or ''
    if not url:
        empty += 1
        print(f'  EMPTY [{r[0]}] {r[1]}')
    elif 'placeholder' in url.lower() or 'placehold' in url.lower() or 'via.placeholder' in url.lower():
        placeholder += 1
        print(f'  PLACEHOLDER [{r[0]}] {r[1]} -> {url[:80]}')
    else:
        real += 1

print(f'\nSummary:')
print(f'  Real images: {real}')
print(f'  Placeholder: {placeholder}')
print(f'  Empty: {empty}')

# Show first 5 real ones as sample
print('\nSample real images:')
cur.execute("""
    SELECT d.name, di.image_url
    FROM destinations d JOIN destination_images di ON d.id=di.destination_id
    WHERE di.image_url NOT LIKE '%placeholder%'
    LIMIT 5
""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1][:100]}')

conn.close()
