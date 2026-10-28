"""Email-safe branding for Main Street AI Brief issues sent via Buttondown (free plan: no custom CSS, so all styling is inline).
v2: full-width navy band (table, bgcolor attr + inline style) with centered logo and full-width orange rule; bold orange links;
boxes built from table cells (bgcolor attr + inline background-color) with explicit dark text; color-scheme light-only hints.
brand(body_html) -> str. Pure string transform; does not touch feed.xml."""
import re
SITE="https://mainstreetaibrief.com/"; LOGO=SITE+"assets/header-lockup@2x.png"   # live, 1555x236, white-on-transparent: needs the navy band
NAVY="#14213D"; OR="#FF6B1A"; PEACH="#FFF1E6"; LINE="#E2DED5"
FONT="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
HINTS=('<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only">'
       '<style>:root{color-scheme:light only;supported-color-schemes:light only}</style>')
HEADER=(HINTS+
 f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{NAVY}" '
 f'style="width:100%;background-color:{NAVY};margin:0 0 20px 0;color-scheme:light only">'
 f'<tr><td align="center" bgcolor="{NAVY}" style="background-color:{NAVY};padding:16px 12px;text-align:center">'
 f'<a href="{SITE}" style="text-decoration:none;color:#FFFFFF"><img src="{LOGO}" width="369" height="56" '
 f'alt="Main Street AI Brief - Daily AI tips for small business owners" '
 f'style="display:block;border:0;outline:none;width:100%;max-width:369px;height:auto;margin:0 auto"></a></td></tr>'
 f'<tr><td height="4" bgcolor="{OR}" style="background-color:{OR};height:4px;line-height:4px;font-size:0;mso-line-height-rule:exactly">&nbsp;</td></tr></table>')
def _box(m):
    inner=m.group(1)
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;margin:12px 0;color-scheme:light only"><tr>'
            f'<td width="4" bgcolor="{OR}" style="width:4px;background-color:{OR};font-size:0;line-height:0">&nbsp;</td>'
            f'<td bgcolor="{PEACH}" style="background-color:{PEACH};color:{NAVY};padding:12px 16px;font-size:15px;line-height:1.5">'
            f'<span style="color:{NAVY}">{inner}</span></td></tr></table>')
def brand(b):
    b=re.sub(r'<h3>(.*?)</h3>', lambda m: f'<h3 style="font-family:{FONT};font-size:17px;letter-spacing:.5px;color:{NAVY};border-left:5px solid {OR};padding:2px 0 2px 10px;margin:26px 0 10px">{m.group(1)}</h3>', b)
    b=re.sub(r'<a href=', f'<a style="color:{OR};font-weight:700" href=', b)
    b=re.sub(r'<blockquote>(.*?)</blockquote>', _box, b, flags=re.S)
    b=b.replace(' border="1" cellpadding="4" style="border-collapse:collapse"', f' width="100%" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;border:1px solid {LINE};font-size:15px"')
    b=b.replace('<th>', f'<th align="left" bgcolor="{NAVY}" style="background-color:{NAVY};color:#FFFFFF;border:1px solid {NAVY};padding:8px">')
    b=b.replace('<td>', f'<td bgcolor="#FFFFFF" style="background-color:#FFFFFF;color:{NAVY};border:1px solid {LINE};padding:8px">')
    b=b.replace('<p><i>', f'<p style="font-size:17px;color:{NAVY}"><i>',1)
    return HEADER+b
