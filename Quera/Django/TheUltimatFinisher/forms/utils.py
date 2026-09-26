from django.http import HttpResponse

import io
import csv
import json
import xlsxwriter
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class FormExporter:
    def __init__(self, form):
        self.form = form
    
    def export_responses_csv(self, responses=None):
        if responses is None:
            responses = self.form.responses.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        
        fields = self.form.fields.all().order_by('order')
        header = ['Response ID', 'Submitted At', 'User', 'IP Address']
        header.extend([field.label for field in fields])
        writer.writerow(header)
        
        
        for response in responses:
            row = [
                response.id,
                response.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                response.submitted_by.username if response.submitted_by else 'Anonymous',
                response.ip_address or ''
            ]
            
            
            response_data = {data.field.id: data.value for data in response.data.all()}
            for field in fields:
                value = response_data.get(field.id, '')
                
                if field.field_type == 'checkbox' and value:
                    try:
                        checkbox_values = json.loads(value)
                        if isinstance(checkbox_values, list):
                            value = ', '.join(checkbox_values)
                    except (json.JSONDecodeError, TypeError):
                        pass
                row.append(value)
            
            writer.writerow(row)
        
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.form.title}_responses.csv"'
        return response
    
    def export_responses_excel(self, responses=None):
        
        if responses is None:
            responses = self.form.responses.all()
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Responses')
        
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'text_wrap': True
        })
        
        
        fields = self.form.fields.all().order_by('order')
        headers = ['Response ID', 'Submitted At', 'User', 'IP Address']
        headers.extend([field.label for field in fields])
        
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        
        for row_num, response in enumerate(responses, 1):
            worksheet.write(row_num, 0, response.id, cell_format)
            worksheet.write(row_num, 1, response.submitted_at.strftime('%Y-%m-%d %H:%M:%S'), cell_format)
            worksheet.write(row_num, 2, response.submitted_by.username if response.submitted_by else 'Anonymous', cell_format)
            worksheet.write(row_num, 3, response.ip_address or '', cell_format)
            
            
            response_data = {data.field.id: data.value for data in response.data.all()}
            for col_num, field in enumerate(fields, 4):
                value = response_data.get(field.id, '')
                
                if field.field_type == 'checkbox' and value:
                    try:
                        checkbox_values = json.loads(value)
                        if isinstance(checkbox_values, list):
                            value = ', '.join(checkbox_values)
                    except (json.JSONDecodeError, TypeError):
                        pass
                worksheet.write(row_num, col_num, value, cell_format)
        
        
        for col_num, header in enumerate(headers):
            worksheet.set_column(col_num, col_num, min(len(header) + 5, 30))
        
        workbook.close()
        output.seek(0)
        
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.form.title}_responses.xlsx"'
        return response
    
    def export_responses_pdf(self, responses=None):
        
        if responses is None:
            responses = self.form.responses.all()
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=(A4[1], A4[0]))  
        styles = getSampleStyleSheet()
        story = []
        
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        )
        story.append(Paragraph(f"Form Responses: {self.form.title}", title_style))
        story.append(Spacer(1, 12))
        
        
        info_style = styles['Normal']
        story.append(Paragraph(f"<b>Total Responses:</b> {responses.count()}", info_style))
        story.append(Paragraph(f"<b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 20))
        
        
        if responses.exists():
            fields = self.form.fields.all().order_by('order')
            
            available_width = A4[1] - 2 * inch  
            max_columns = min(len(fields) + 3, 8)  
            
            
            table_data = []
            headers = ['ID', 'Date', 'User']
            
            display_fields = fields[:max_columns-3] if len(fields) > max_columns-3 else fields
            headers.extend([field.label[:15] for field in display_fields])  
            table_data.append(headers)
            
            for response in responses[:50]:  
                row = [
                    str(response.id),
                    response.submitted_at.strftime('%m/%d'),  
                    response.submitted_by.username[:10] if response.submitted_by else 'Anon'  
                ]
                
                response_data = {data.field.id: data.value for data in response.data.all()}
                for field in display_fields:
                    value = response_data.get(field.id, '')
                    if field.field_type == 'checkbox' and value:
                        try:
                            checkbox_values = json.loads(value)
                            if isinstance(checkbox_values, list):
                                value = ', '.join(checkbox_values)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    if len(str(value)) > 20:
                        value = str(value)[:17] + '...'
                    row.append(str(value))
                
                table_data.append(row)
            
            num_cols = len(headers)
            col_width = available_width / num_cols
            col_widths = [col_width] * num_cols
            
            
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),  
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),  
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(table)
            
            if len(fields) > max_columns-3:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"<i>Note: Showing {len(display_fields)} of {len(fields)} fields. Export to Excel for complete data.</i>", styles['Italic']))
            
            if responses.count() > 50:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"<i>Note: Only first 50 responses shown. Total responses: {responses.count()}</i>", styles['Italic']))
        else:
            story.append(Paragraph("No responses found.", styles['Normal']))
        
        doc.build(story)
        output.seek(0)
        
        
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{self.form.title}_responses.pdf"'
        return response
