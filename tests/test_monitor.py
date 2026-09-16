"""Unit tests for the HTML scraping and link extraction engine."""

from monitor import parse_directory_listing

SAMPLE_APACHE_HTML = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
 <head>
  <title>Index of /DOC/Preselections/Cycle_Masters/LISTES_CONCOURS_ECRIT</title>
 </head>
 <body>
<h1>Index of /DOC/Preselections/Cycle_Masters/LISTES_CONCOURS_ECRIT</h1>
  <table>
   <tr><th valign="top"><img src="/icons/blank.gif" alt="[ICO]"></th><th><a href="?C=N;O=D">Name</a></th><th><a href="?C=M;O=A">Last modified</a></th><th><a href="?C=S;O=A">Size</a></th><th><a href="?C=D;O=A">Description</a></th></tr>
   <tr><th colspan="5"><hr></th></tr>
<tr><td valign="top"><img src="/icons/back.gif" alt="[PARENTDIR]"></td><td><a href="/DOC/Preselections/Cycle_Masters/">Parent Directory</a></td><td>&nbsp;</td><td align="right">  - </td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/pdf.gif" alt="[   ]"></td><td><a href="Master_IT_TAM.pdf">Master_IT_TAM.pdf</a></td><td align="right">2026-09-16 16:07  </td><td align="right">166K</td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/pdf.gif" alt="[   ]"></td><td><a href="Master_MIN_TN.pdf">Master_MIN_TN.pdf</a></td><td align="right">2026-09-16 16:05  </td><td align="right">437K</td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/text.gif" alt="[   ]"></td><td><a href="readme.txt">readme.txt</a></td><td align="right">2026-09-16 12:00  </td><td align="right">1.2K</td><td>&nbsp;</td></tr>
   <tr><th colspan="5"><hr></th></tr>
</table>
</body></html>
"""


def test_parse_directory_listing_extracts_pdfs_only():
    base_url = "https://example.university.edu/admissions/results/"
    results = parse_directory_listing(SAMPLE_APACHE_HTML, base_url)

    filenames = [item.filename for item in results]
    assert "Master_IT_TAM.pdf" in filenames
    assert "Master_MIN_TN.pdf" in filenames
    assert "readme.txt" not in filenames  # Default watcher filters for .pdf
    assert "Parent Directory" not in filenames

    # Verify absolute URL construction
    item_map = {item.filename: item.url for item in results}
    assert item_map["Master_IT_TAM.pdf"] == "https://example.university.edu/admissions/results/Master_IT_TAM.pdf"


def test_parse_directory_listing_handles_root_relative_paths():
    html = '<a href="/files/Master_TEST.pdf">Test</a>'
    base = "https://example.university.edu/admissions/"
    results = parse_directory_listing(html, base)

    assert len(results) == 1
    assert results[0].filename == "Master_TEST.pdf"
    assert results[0].url == "https://example.university.edu/files/Master_TEST.pdf"
