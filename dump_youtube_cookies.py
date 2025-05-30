import browser_cookie3

# Extract cookies from Chrome for youtube.com
cookies = browser_cookie3.chrome(domain_name='youtube.com')

# Save in Netscape format
with open('youtube_cookies.txt', 'w', encoding='utf-8') as f:
    f.write('# Netscape HTTP Cookie File\n')
    for c in cookies:
        f.write(
            f"{c.domain}\t"
            f"{'TRUE' if c.domain.startswith('.') else 'FALSE'}\t"
            f"{c.path}\t"
            f"{'TRUE' if c.secure else 'FALSE'}\t"
            f"{int(c.expires or 0)}\t"
            f"{c.name}\t"
            f"{c.value}\n"
        )
