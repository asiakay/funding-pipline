from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def build_pdf(df, out_path, max_results: int = 5) -> None:
    """Generate a simple one-pager PDF of top opportunities.

    Parameters
    ----------
    df : pandas.DataFrame
        Scored opportunities. Expected to contain ``Rank`` and ``Grant Name``
        columns.
    out_path : str
        File path where the PDF should be written.
    max_results : int, optional
        Maximum number of opportunities to include. Defaults to 5.
    """
    c = canvas.Canvas(out_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "EQORE Top Opportunities")

    c.setFont("Helvetica", 11)
    y = height - 108
    for _, row in df.head(max_results).iterrows():
        text = f"{int(row['Rank'])}. {row['Grant Name']} (Score: {row['Weighted Score']:.1f})"
        c.drawString(72, y, text)
        y -= 14
        if y < 72:
            c.showPage()
            y = height - 72

    c.save()
