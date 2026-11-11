# Email templates for Paytm AI Sales Teammate

PAYTM_BLUE = "#002970"
PAYTM_LIGHT_BLUE = "#00BAF2"
PAYTM_WHITE = "#FFFFFF"


def get_base_email_template(content: str, merchant_name: str) -> str:
    """Wraps content in the Paytm-branded email shell."""
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Paytm for Business</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:20px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color:{PAYTM_BLUE};padding:24px 32px;text-align:center;">
              <h1 style="color:{PAYTM_WHITE};margin:0;font-size:24px;letter-spacing:1px;">
                <span style="color:{PAYTM_LIGHT_BLUE};">Pay</span>tm for Business
              </h1>
              <p style="color:#a0b4d4;margin:4px 0 0;font-size:13px;">Your Growth Partner</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              {content}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color:#f8f9fa;padding:20px 32px;border-top:1px solid #e0e0e0;text-align:center;">
              <p style="color:#888;font-size:12px;margin:0;">
                Paytm for Business | <a href="https://paytm.com/business" style="color:{PAYTM_LIGHT_BLUE};text-decoration:none;">paytm.com/business</a>
              </p>
              <p style="color:#aaa;font-size:11px;margin:6px 0 0;">
                You're receiving this because you were identified as a potential Paytm merchant partner.<br>
                <a href="#" style="color:#aaa;">Unsubscribe</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_outreach_email_content(lead: dict) -> tuple[str, str]:
    """
    Returns (subject, html_body) for the initial outreach email.
    Personalized based on lead's business type and pain points.
    """
    name = lead.get("name", "").split()[0]  # First name
    business = lead.get("business", "your business")
    business_type = lead.get("business_type", "business")
    city = lead.get("city", "")
    pain_points = lead.get("pain_points", [])
    current_payment = lead.get("current_payment_method", "")

    # Choose primary product recommendation based on business type
    product_highlight = _get_product_highlight(business_type, pain_points)
    pain_point_str = pain_points[0] if pain_points else "managing digital payments"

    subject = f"Grow {business} with Paytm — Free Setup, No Charges! 🚀"

    content = f"""
      <h2 style="color:{PAYTM_BLUE};margin:0 0 16px;">Namaste {name} ji! 🙏</h2>
      
      <p style="color:#333;font-size:15px;line-height:1.6;">
        Paytm Business Team se connect kar rahe hain. Maine dekha ki aap <strong>{business}</strong> ({business_type}) 
        chalate hain {city} mein — aur main chahti hun ki aapka business aur bhi tez grow kare! 🚀
      </p>

      <p style="color:#555;font-size:14px;line-height:1.6;">
        Aaj kal <strong>"{pain_point_str}"</strong> jaise problems bahut merchants face karte hain. 
        Paytm ne iske liye kuch amazing solutions banaye hain jo specifically aap jaise {business_type} owners ke liye hain.
      </p>

      <!-- Product Highlight Box -->
      <div style="background:linear-gradient(135deg,{PAYTM_BLUE},{PAYTM_LIGHT_BLUE});border-radius:8px;padding:20px;margin:20px 0;color:white;">
        {product_highlight}
      </div>

      <!-- Benefits -->
      <h3 style="color:{PAYTM_BLUE};font-size:16px;">Paytm se aapko milega:</h3>
      <table cellpadding="0" cellspacing="0" width="100%">
        <tr>
          <td style="padding:8px 0;vertical-align:top;width:28px;font-size:18px;">✅</td>
          <td style="padding:8px 0;color:#333;font-size:14px;"><strong>FREE Paytm QR Code</strong> — Sab UPI apps ka ek QR, ₹0 mein</td>
        </tr>
        <tr>
          <td style="padding:8px 0;vertical-align:top;font-size:18px;">🔊</td>
          <td style="padding:8px 0;color:#333;font-size:14px;"><strong>Soundbox FREE</strong> — Payment aate hi awaaz, koi miss nahi hoga</td>
        </tr>
        <tr>
          <td style="padding:8px 0;vertical-align:top;font-size:18px;">💳</td>
          <td style="padding:8px 0;color:#333;font-size:14px;"><strong>POS Machine</strong> — Best MDR rates, card + UPI sab accept karo</td>
        </tr>
        <tr>
          <td style="padding:8px 0;vertical-align:top;font-size:18px;">💰</td>
          <td style="padding:8px 0;color:#333;font-size:14px;"><strong>Business Loan</strong> — ₹10K to ₹50L, no collateral, 24hr approval</td>
        </tr>
      </table>

      <!-- CTA -->
      <div style="text-align:center;margin:28px 0 16px;">
        <a href="https://paytm.com/business/demo" 
           style="background-color:{PAYTM_LIGHT_BLUE};color:white;text-decoration:none;padding:14px 32px;border-radius:6px;font-size:16px;font-weight:bold;display:inline-block;">
          Book FREE 15-Min Demo →
        </a>
      </div>
      <div style="text-align:center;margin-bottom:24px;">
        <a href="https://paytm.com/business" 
           style="color:{PAYTM_BLUE};font-size:13px;text-decoration:underline;">
          Ya seedha signup karein — paytm.com/business
        </a>
      </div>

      <p style="color:#555;font-size:14px;line-height:1.6;">
        Koi bhi sawaal ho toh WhatsApp pe reply karein ya mujhe direct message karein. 
        Main personally har sawaal ka jawab dungi! 😊
      </p>

      <p style="color:#333;font-size:14px;margin-top:20px;">
        Warm regards,<br>
        <strong style="color:{PAYTM_BLUE};">Paytm AI Sales Teammate</strong><br>
        <span style="color:#888;font-size:12px;">AI Sales Teammate, Paytm for Business</span><br>
        <span style="color:{PAYTM_LIGHT_BLUE};font-size:12px;">📱 WhatsApp: +91-XXXXX-XXXXX</span>
      </p>
    """

    return subject, get_base_email_template(content, name)


def get_follow_up_email_content(lead: dict, follow_up_number: int) -> tuple[str, str]:
    """
    Returns (subject, html_body) for follow-up emails.
    """
    name = lead.get("name", "").split()[0]
    business = lead.get("business", "your business")
    business_type = lead.get("business_type", "business")

    subjects = {
        1: f"Quick follow-up: Paytm ke baare mein kuch sawaal? 🤔",
        2: f"Ramesh ji, sirf 2 min — Paytm FREE demo dekh lo! ⏰",
        3: f"Last call: Exclusive offer for {business} — expires soon! 🎁",
    }
    subject = subjects.get(follow_up_number, f"Still thinking? Paytm is here to help! 🙏")

    messages = {
        1: f"""
          <p style="color:#333;font-size:15px;line-height:1.6;">
            {name} ji, namaskar! 🙏<br><br>
            Maine pehle aapko Paytm ke baare mein bata thi. Bas check kar rahi thi ki aapko 
            koi sawaal tha ya nahi?<br><br>
            Agar aap chahein toh main ek <strong>FREE 15-minute demo</strong> arrange kar sakti hun — 
            koi pressure nahi, bas dekhne ke liye ki Paytm <strong>{business}</strong> ke liye 
            kaise helpful ho sakta hai.
          </p>
        """,
        2: f"""
          <p style="color:#333;font-size:15px;line-height:1.6;">
            {name} ji, ek khaas baat share karna chahti thi! 🌟<br><br>
            Aap jaise {business_type} owners ke liye Paytm ne recently ek special offer launch kiya hai:<br>
          </p>
          <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:16px;border-radius:4px;margin:16px 0;">
            <strong>🎁 Special Offer:</strong> Paytm Soundbox ke saath pehle 3 mahine ke transactions pe 
            <strong>0% MDR</strong>! (Limited time offer)
          </div>
          <p style="color:#555;font-size:14px;">
            Aur yaad rahe — Paytm QR Code hamesha FREE hai, koi hidden charges nahi!
          </p>
        """,
        3: f"""
          <p style="color:#333;font-size:15px;line-height:1.6;">
            {name} ji, yeh mera aakhri follow-up message hai. 😊<br><br>
            Main samajhti hun ki aap busy rehte hain — isliye bilkul pressure nahi.
            Bas yeh jaanna chahti thi ki agar koi specific reason hai Paytm join na karne ka, 
            toh main use solve karne ki koshish karun?<br><br>
            Agar kabhi bhi zarorat ho toh main hamesha yahan hun! Paytm family mein aapka 
            swagat hai. 🙏
          </p>
        """,
    }

    content = messages.get(follow_up_number, messages[1])
    content += f"""
      <div style="text-align:center;margin:24px 0;">
        <a href="https://paytm.com/business/demo" 
           style="background-color:{PAYTM_LIGHT_BLUE};color:white;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:15px;font-weight:bold;display:inline-block;">
          Book FREE Demo →
        </a>
      </div>
      <p style="color:#333;font-size:14px;">
        Warm regards,<br>
        <strong style="color:{PAYTM_BLUE};">Paytm AI Sales Teammate</strong><br>
        <span style="color:#888;font-size:12px;">AI Sales Teammate, Paytm for Business</span>
      </p>
    """

    return subject, get_base_email_template(content, name)


def _get_product_highlight(business_type: str, pain_points: list) -> str:
    """Returns product highlight HTML based on business type."""
    business_lower = business_type.lower()
    pain_lower = " ".join(pain_points).lower()

    if "kirana" in business_lower or "general store" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">🔊 Paytm Soundbox — Perfect for Kirana Stores!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Jab bhi koi payment aaye — PhonePe, GPay, ya koi bhi UPI app se — Soundbox oonchi awaaz mein bolega!
            ₹0 rental, sirf ek baar refundable deposit.
          </p>
        """
    elif "medical" in business_lower or "pharmacy" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">💳 Paytm POS + Smart Billing Solution!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Medical stores ke liye Paytm POS best solution hai — card, UPI, sab ek jagah.
            Plus detailed reports jo aapki daily sales track karti hain automatically!
          </p>
        """
    elif "restaurant" in business_lower or "food" in business_lower or "biryani" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">🍽️ Paytm Restaurant Solution — Faster Billing!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Paytm POS se restaurant billing super fast ho jati hai. 
            Plus Paytm Business Loan se aap apna restaurant expand kar sakte hain bina collateral ke!
          </p>
        """
    elif "cloth" in business_lower or "fashion" in business_lower or "apparel" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">💳 Paytm POS — Low MDR, High Customer Satisfaction!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Kapde ki dukaan ke liye EMI option bahut zaroori hai. Paytm POS se customers ko 
            easy EMI milti hai aur aapka MDR bhi kam rehta hai — industry best rates!
          </p>
        """
    elif "petrol" in business_lower or "fuel" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">⛽ Paytm All-in-One — One QR for Everything!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Petrol pump pe alag-alag QR codes ka jhanjhat khatam! Paytm ka ek QR code 
            sab UPI apps accept karta hai. Plus instant settlement aur business loan bhi available!
          </p>
        """
    elif "salon" in business_lower or "beauty" in business_lower or "parlour" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">💅 Paytm QR — FREE Digital Payments Start Today!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Beauty salons ke liye Paytm QR code bilkul FREE hai! Customers PhonePe, GPay, 
            ya Paytm se pay kar sakte hain — koi monthly fees nahi!
          </p>
        """
    elif "electronic" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">📱 Paytm POS + EMI — Sell More, Earn More!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Electronics ke liye Paytm POS se customers ko easy EMI milti hai, 
            jisse high-value items bhi asani se bikti hain. Plus business loan for inventory!
          </p>
        """
    elif "sweet" in business_lower or "mithai" in business_lower:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">🍬 Paytm Soundbox — Festival Season Ka Best Friend!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            Diwali, Eid, Holi — festival season mein rush hoga. Paytm Soundbox se 
            har payment ki awaaz sunai degi, koi payment miss nahi hoga!
          </p>
        """
    else:
        return """
          <h3 style="margin:0 0 8px;font-size:16px;">🚀 Paytm Business — Complete Payment Solution!</h3>
          <p style="margin:0;font-size:14px;opacity:0.9;">
            QR Code (FREE), Soundbox, POS Machine, aur Business Loan — 
            sab kuch ek jagah, aur setup bilkul aasaan!
          </p>
        """
