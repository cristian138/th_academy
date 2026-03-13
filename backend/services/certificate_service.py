"""
Certificate Generation Service
Generates labor certificates for contracts with QR verification
"""
import io
import os
import uuid
import qrcode
from datetime import datetime
from fpdf import FPDF
from typing import Optional
import logging
import pytz

logger = logging.getLogger(__name__)

# Colombia timezone
COLOMBIA_TZ = pytz.timezone('America/Bogota')

class CertificatePDF(FPDF):
    def __init__(self, logo_path: Optional[str] = None):
        super().__init__()
        self.logo_path = logo_path
        self.set_auto_page_break(auto=True, margin=25)
        
    def header(self):
        # Solo mostrar header en la primera página
        if self.page_no() == 1:
            # Logo centrado
            if self.logo_path and os.path.exists(self.logo_path):
                page_width = self.w
                logo_width = 30
                x_position = (page_width - logo_width) / 2
                self.image(self.logo_path, x=x_position, y=8, w=logo_width)
                self.ln(25)
            
            # Company name
            self.set_font('Helvetica', 'B', 13)
            self.set_text_color(0, 45, 84)
            self.cell(0, 5, 'ACADEMIA JOTUNS CLUB SAS', 0, 1, 'C')
            
            self.set_font('Helvetica', '', 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 4, 'NIT: 901.863.346-4', 0, 1, 'C')
            self.cell(0, 4, 'Calle 4 #4-46, Sesquile, Cundinamarca', 0, 1, 'C')
            self.cell(0, 4, 'Telefono: 311 454 0684', 0, 1, 'C')
            
            # Line separator
            self.ln(2)
            self.set_draw_color(0, 45, 84)
            self.set_line_width(0.4)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(6)
    
    def footer(self):
        self.set_y(-18)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 3, f'Pagina {self.page_no()}', 0, 0, 'C')


class CertificateService:
    def __init__(self):
        self.logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png')
        self.signature_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'signature.png')
        self.qr_temp_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'temp_qr.png')
        # Create assets directory if not exists
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        os.makedirs(assets_dir, exist_ok=True)
    
    def _format_currency(self, amount: float) -> str:
        """Format amount as Colombian pesos"""
        return f"${amount:,.0f} COP".replace(",", ".")
    
    def _format_date(self, date) -> str:
        """Format date in Spanish"""
        months = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        
        # Handle None
        if date is None:
            return "INDEFINIDO"
        
        # Handle empty string
        if isinstance(date, str) and date.strip() == '':
            return "INDEFINIDO"
        
        # Handle string dates
        if isinstance(date, str):
            try:
                # Try ISO format
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            except:
                try:
                    # Try other common formats
                    from dateutil import parser
                    date = parser.parse(date)
                except:
                    try:
                        # Try simple date format
                        date = datetime.strptime(date.split('T')[0], '%Y-%m-%d')
                    except:
                        logger.error(f"Could not parse date: {date}")
                        return "INDEFINIDO"
        
        # Handle datetime object
        try:
            return f"{date.day} de {months[date.month]} de {date.year}"
        except Exception as e:
            logger.error(f"Error formatting date {date}: {e}")
            return "INDEFINIDO"
    
    def _number_to_words(self, number: float) -> str:
        """Convert number to Spanish words"""
        units = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
        tens = ['', 'DIEZ', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
        teens = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISEIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE']
        hundreds = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']
        
        n = int(number)
        if n == 0:
            return 'CERO'
        if n == 100:
            return 'CIEN'
        
        result = []
        
        if n >= 1000000:
            millions = n // 1000000
            if millions == 1:
                result.append('UN MILLON')
            else:
                result.append(f'{self._number_to_words(millions)} MILLONES')
            n = n % 1000000
        
        if n >= 1000:
            thousands = n // 1000
            if thousands == 1:
                result.append('MIL')
            else:
                result.append(f'{self._number_to_words(thousands)} MIL')
            n = n % 1000
        
        if n >= 100:
            result.append(hundreds[n // 100])
            n = n % 100
        
        if n >= 20:
            if n % 10 == 0:
                result.append(tens[n // 10])
            else:
                result.append(f'{tens[n // 10]} Y {units[n % 10]}')
        elif n >= 10:
            result.append(teens[n - 10])
        elif n > 0:
            result.append(units[n])
        
        return ' '.join(result)
    
    def _generate_qr_code(self, verification_code: str, verification_url: str) -> str:
        """Generate QR code image and return path"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(self.qr_temp_path)
        return self.qr_temp_path
    
    def generate_labor_certificate(
        self,
        collaborator_name: str,
        collaborator_id: str,
        contract_title: str,
        contract_description: str,
        contract_type: str,
        start_date,
        end_date,
        monthly_payment: Optional[float],
        payment_per_session: Optional[float],
        legal_rep_name: str = "Representante Legal",
        verification_code: str = None,
        verification_url: str = None
    ) -> bytes:
        """Generate a labor certificate PDF with QR verification"""
        
        # Generate verification code if not provided
        if not verification_code:
            verification_code = str(uuid.uuid4())[:12].upper()
        
        if not verification_url:
            verification_url = f"https://th.academiajotuns.com/verificar/{verification_code}"
        
        pdf = CertificatePDF(self.logo_path if os.path.exists(self.logo_path) else None)
        pdf.add_page()
        
        # Title
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 45, 84)
        pdf.cell(0, 8, 'CERTIFICADO LABORAL', 0, 1, 'C')
        
        # Subtitle
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 5, 'CONTRATO POR PRESTACION DE SERVICIOS', 0, 1, 'C')
        pdf.ln(5)
        
        # Introduction
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 4, 
            'El suscrito Representante Legal de ACADEMIA JOTUNS CLUB SAS, ' +
            'sociedad legalmente constituida, identificada con NIT 901.863.346-4, certifica que:'
        )
        pdf.ln(4)
        
        # Collaborator info
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 5, f'{collaborator_name.upper()}', 0, 1, 'C')
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 4, f'Identificado(a) con documento No. {collaborator_id}', 0, 1, 'C')
        pdf.ln(4)
        
        # Contract statement
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 4,
            'PRESTA sus servicios a nuestra organizacion mediante CONTRATO DE PRESTACION DE SERVICIOS.'
        )
        pdf.ln(3)
        
        # Vigencia del contrato
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 5, 'VIGENCIA DEL CONTRATO:', 0, 1, 'L')
        pdf.set_font('Helvetica', '', 9)
        
        # Fecha de inicio
        pdf.cell(50, 4, 'Fecha de inicio:', 0, 0, 'L')
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 4, self._format_date(start_date).upper(), 0, 1, 'L')
        
        # Fecha de finalización
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(50, 4, 'Fecha de finalizacion:', 0, 0, 'L')
        pdf.set_font('Helvetica', 'B', 9)
        end_date_text = self._format_date(end_date).upper() if end_date else "INDEFINIDO"
        pdf.cell(0, 4, end_date_text, 0, 1, 'L')
        pdf.ln(3)
        
        # OBJETO
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 5, 'OBJETO:', 0, 1, 'L')
        pdf.set_font('Helvetica', '', 8)
        objeto_text = contract_description if contract_description else contract_title
        pdf.multi_cell(0, 4, objeto_text)
        pdf.ln(3)
        
        # HONORARIOS
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 5, 'HONORARIOS:', 0, 1, 'L')
        pdf.set_font('Helvetica', '', 9)
        
        if payment_per_session and payment_per_session > 0:
            amount_words = self._number_to_words(payment_per_session)
            pdf.multi_cell(0, 4,
                f'El contratista recibe honorarios por valor de {self._format_currency(payment_per_session)} ' +
                f'({amount_words} PESOS M/CTE) por cada sesion o servicio prestado.'
            )
        elif monthly_payment and monthly_payment > 0:
            amount_words = self._number_to_words(monthly_payment)
            pdf.multi_cell(0, 4,
                f'El contratista recibe honorarios mensuales por valor de {self._format_currency(monthly_payment)} ' +
                f'({amount_words} PESOS M/CTE).'
            )
        pdf.ln(3)
        
        # NOTA
        pdf.set_font('Helvetica', 'I', 7)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 3,
            'NOTA: El presente contrato es de naturaleza civil y no genera relacion laboral. ' +
            'El contratista es responsable del pago de sus propias obligaciones de seguridad social ' +
            '(salud, pension y ARL) conforme a la normatividad vigente.'
        )
        pdf.ln(4)
        
        # Expedición
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)
        today = datetime.now()
        pdf.multi_cell(0, 4,
            f'Se expide el presente certificado a solicitud del interesado, en el municipio de Sesquile, Cundinamarca, ' +
            f'a los {today.day} dias del mes de {self._format_date(today).split(" de ")[1].split(" de ")[0]} de {today.year}.'
        )
        pdf.ln(8)
        
        # Signature section - asegurar que haya espacio suficiente
        space_needed = 60  # espacio necesario para firma + QR
        if pdf.get_y() > (297 - 25 - space_needed):  # A4 height - margin - space
            pdf.add_page()
            pdf.ln(10)
        
        # Firma
        if os.path.exists(self.signature_path):
            page_width = pdf.w
            img_width = 40
            x_position = (page_width - img_width) / 2
            pdf.image(self.signature_path, x=x_position, y=pdf.get_y(), w=img_width)
            pdf.ln(18)
        else:
            pdf.cell(0, 4, '____________________________________', 0, 1, 'C')
            pdf.ln(2)
        
        # Texto de firma
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 4, legal_rep_name.upper(), 0, 1, 'C')
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(0, 3, 'Representante Legal', 0, 1, 'C')
        pdf.cell(0, 3, 'ACADEMIA JOTUNS CLUB SAS', 0, 1, 'C')
        pdf.cell(0, 3, 'NIT 901.863.346-4', 0, 1, 'C')
        pdf.ln(6)
        
        # QR Code section
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)
        
        # Generate QR
        qr_path = self._generate_qr_code(verification_code, verification_url)
        
        # QR y texto de verificación lado a lado
        y_before_qr = pdf.get_y()
        pdf.image(qr_path, x=15, y=y_before_qr, w=25)
        
        pdf.set_xy(45, y_before_qr)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(0, 4, 'VERIFICACION DEL DOCUMENTO', 0, 1, 'L')
        pdf.set_x(45)
        pdf.set_font('Helvetica', '', 7)
        pdf.cell(0, 3, f'Codigo de verificacion: {verification_code}', 0, 1, 'L')
        pdf.set_x(45)
        pdf.cell(0, 3, 'Escanee el codigo QR o visite:', 0, 1, 'L')
        pdf.set_x(45)
        pdf.set_font('Helvetica', 'I', 7)
        pdf.set_text_color(0, 45, 84)
        pdf.cell(0, 3, verification_url, 0, 1, 'L')
        
        # Cleanup temp QR file
        try:
            if os.path.exists(qr_path):
                os.remove(qr_path)
        except:
            pass
        
        return bytes(pdf.output()), verification_code


certificate_service = CertificateService()
