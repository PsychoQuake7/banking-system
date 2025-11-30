from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

def render_to_pdf(template_src, context_dict={}):
    """
    Render a Django template to PDF using xhtml2pdf.
    
    Args:
        template_src: Path to the template file
        context_dict: Context dictionary for the template
        
    Returns:
        HttpResponse object with PDF content or None if error
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    
    result = BytesIO()
    
    # Generate PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="report.pdf"'
        return response
    
    return None
