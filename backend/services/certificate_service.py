"""
Certificate Generation Service
Generates labor certificates for contracts
"""
import io
import os
from datetime import datetime
from fpdf import FPDF
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CertificatePDF(FPDF):
    def __init__(self, logo_path: Optional[str] = None):
        super().__init__()
        self.logo_path = logo_path
        
    def header(self):
        # Logo
        if self.logo_path and os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 8, 40)
        
        # Company name
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 45, 84)  # #002d54
        self.cell(0, 10, 'ACADEMIA JOTUNS CLUB SAS', 0, 1, 'C')
        
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'NIT: 901.863.346-4', 0, 1, 'C')
        self.cell(0, 5, 'Calle 4 #4-46, Sesquile, Cundinamarca', 0, 1, 'C')
        self.cell(0, 5, 'Telefono: 311 454 0684', 0, 1, 'C')
        
        # Line separator
        self.ln(5)
        self.set_draw_color(0, 45, 84)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def footer(self):
        self.set_y(-25)
        self.set_draw_color(0, 45, 84)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 4, 'Este certificado se expide a solicitud del interesado.', 0, 1, 'C')
        self.cell(0, 4, 'Academia Jotuns Club SAS - NIT 901.863.346-4', 0, 1, 'C')


class CertificateService:
    def __init__(self):
        self.logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png')
        # Create assets directory if not exists
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        os.makedirs(assets_dir, exist_ok=True)
    
    def _format_currency(self, amount: float) -> str:
        """Format amount as Colombian pesos"""
        return f"${amount:,.0f} COP".replace(",", ".")
    
    def _format_date(self, date: datetime) -> str:
        """Format date in Spanish"""
        months = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        return f"{date.day} de {months[date.month]} de {date.year}"
    
    def _number_to_words(self, number: float) -> str:
        """Convert number to Spanish words (simplified)"""
        # Simplified version for common amounts
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
        
        # Millions
        if n >= 1000000:
            millions = n // 1000000
            if millions == 1:
                result.append('UN MILLON')
            else:
                result.append(f'{self._number_to_words(millions)} MILLONES')
            n = n % 1000000
        
        # Thousands
        if n >= 1000:
            thousands = n // 1000
            if thousands == 1:
                result.append('MIL')
            else:
                result.append(f'{self._number_to_words(thousands)} MIL')
            n = n % 1000
        
        # Hundreds
        if n >= 100:
            result.append(hundreds[n // 100])
            n = n % 100
        
        # Tens and units
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
    
    def generate_labor_certificate(
        self,
        collaborator_name: str,
        collaborator_id: str,
        contract_title: str,
        contract_type: str,
        start_date: datetime,
        end_date: Optional[datetime],
        monthly_payment: Optional[float],
        payment_per_session: Optional[float],
        legal_rep_name: str = "Representante Legal"
    ) -> bytes:
        """Generate a labor certificate PDF"""
        
        pdf = CertificatePDF(self.logo_path if os.path.exists(self.logo_path) else None)
        pdf.add_page()
        
        # Title
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(0, 45, 84)
        pdf.cell(0, 15, 'CERTIFICADO LABORAL', 0, 1, 'C')
        pdf.ln(5)
        
        # Subtitle - Contract type
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 45, 84)
        pdf.cell(0, 8, 'CONTRATO POR PRESTACION DE SERVICIOS', 0, 1, 'C')
        pdf.ln(10)
        
        # Certificate body
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(0, 0, 0)
        
        # Introduction
        pdf.multi_cell(0, 7, 
            'El suscrito Representante Legal de ACADEMIA JOTUNS CLUB SAS, ' +
            'sociedad legalmente constituida, identificada con NIT 901.XXX.XXX-X, certifica que:'
        )
        pdf.ln(8)
        
        # Collaborator info
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 7, f'{collaborator_name.upper()}', 0, 1, 'C')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, f'Identificado(a) con documento No. {collaborator_id}', 0, 1, 'C')
        pdf.ln(8)
        
        # Contract details
        pdf.set_font('Helvetica', '', 11)
        
        # Build the certificate text
        if end_date:
            period_text = f"desde el {self._format_date(start_date)} hasta el {self._format_date(end_date)}"
            status_text = "presto"
        else:
            period_text = f"desde el {self._format_date(start_date)} hasta la fecha"
            status_text = "presta"
        
        pdf.multi_cell(0, 7,
            f'{status_text.upper()} sus servicios a nuestra organizacion mediante CONTRATO DE PRESTACION DE SERVICIOS, ' +
            f'{period_text}, desempenando labores relacionadas con: {contract_title}.'
        )
        pdf.ln(5)
        
        # Payment information
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 10, 'INFORMACION DE HONORARIOS:', 0, 1, 'L')
        pdf.set_font('Helvetica', '', 11)
        
        if payment_per_session and payment_per_session > 0:
            amount_words = self._number_to_words(payment_per_session)
            pdf.multi_cell(0, 7,
                f'El contratista recibe honorarios por valor de {self._format_currency(payment_per_session)} ' +
                f'({amount_words} PESOS M/CTE) por cada sesion o servicio prestado.'
            )
        elif monthly_payment and monthly_payment > 0:
            amount_words = self._number_to_words(monthly_payment)
            pdf.multi_cell(0, 7,
                f'El contratista recibe honorarios mensuales por valor de {self._format_currency(monthly_payment)} ' +
                f'({amount_words} PESOS M/CTE).'
            )
        
        pdf.ln(10)
        
        # Legal note
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 6,
            'NOTA: El presente contrato es de naturaleza civil y no genera relacion laboral. ' +
            'El contratista es responsable del pago de sus propias obligaciones de seguridad social ' +
            '(salud, pension y ARL) conforme a la normatividad vigente.'
        )
        pdf.ln(15)
        
        # Issue statement
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(0, 0, 0)
        today = datetime.now()
        pdf.multi_cell(0, 7,
            f'Se expide el presente certificado a solicitud del interesado, en la ciudad de Bogota D.C., ' +
            f'a los {today.day} dias del mes de {self._format_date(today).split(" de ")[1].split(" de ")[0]} de {today.year}.'
        )
        pdf.ln(20)
        
        # Signature
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 7, '____________________________________', 0, 1, 'C')
        pdf.cell(0, 7, legal_rep_name.upper(), 0, 1, 'C')
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 5, 'Representante Legal', 0, 1, 'C')
        pdf.cell(0, 5, 'ACADEMIA JOTUNS CLUB SAS', 0, 1, 'C')
        
        # Return PDF as bytes
        return bytes(pdf.output())


certificate_service = CertificateService()
