from pptx import Presentation

def build_deck(df, out_path):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "EQORE Funding Deck"
    slide.placeholders[1].text = "Auto-generated deck"

    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Top Opportunities"
    text = "\n".join([f"{row['Rank']}. {row['Grant Name']} ({row['Weighted Score']})" for _, row in df.iterrows()])
    slide.placeholders[1].text = text

    prs.save(out_path)
