def find_crc(kw_num: str) -> int:
    """
    Calculate checksum for the given KW number.

    Args:
        kw_num: KW number to be checked.

    Returns:
         (int) Valid KW number checksum (0-9).
    """
    if "/" in kw_num:
        kw_num = kw_num.replace("/", "")
    k = 12
    # g = 5
    f = 4
    a = "ABCDEFGHIJKLMNOPRSTUWYZ"
    results = (1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7)
    j = (0, 1, 3)
    d = 0
    c = kw_num.upper()
    for h in j:
        b = a.find(c[h])
        d += (b + 1) * results[h]
    if c[2].isdigit():
        d += int(c[2]) * results[2]
    else:
        b = a.find(c[2])
        d += (b + 1) * results[2]
    for e in range(f, k):
        d += int(c[e]) * results[e]
    return d % 10
