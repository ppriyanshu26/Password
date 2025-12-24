import tkinter as tk
from pathlib import Path
from openpyxl import Workbook
from classes import Crypto
from credentials import load_vault

def export_credentials_to_excel(master_key):
    desktop_path = Path.home() / "Desktop"
    file_path = desktop_path / "credentials.xlsx"
    
    wb = Workbook()
    ws = wb.active
    ws['A1'], ws['B1'], ws['C1'], ws['D1'] = "Platform", "Username", "Password", "MFA"
    
    crypto = Crypto(master_key)
    vault = load_vault()
    row = 2
    
    for platform, accounts in vault.items():
        for account in accounts:
            ws[f'A{row}'] = platform
            ws[f'B{row}'] = account['username']
            ws[f'C{row}'] = crypto.decrypt_aes(account['password'])
            ws[f'D{row}'] = crypto.decrypt_aes(account['mfa']) if account.get('mfa') else ""
            row += 1
    
    for col in ['A', 'B', 'C', 'D']:
        ws.column_dimensions[col].width = 25
    
    wb.save(file_path)
    return {"success": True, "message": "Exported successfully", "file_path": str(file_path)}
