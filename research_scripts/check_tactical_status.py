import pandas as pd
from src.data.data_loader import DataLoader

def check_current_week_detail():
    loader = DataLoader()
    data = loader.download('NQ', start_date='2026-02-01')
    
    # Get this week data (Feb 9 to today)
    this_week = data[data.index >= '2026-02-09']
    print("\n--- DETALLE DE LA SEMANA ACTUAL (NQ) ---")
    print(this_week[['open', 'high', 'low', 'close']])
    
    # Midpoint W1-W2 (from previous run)
    midpoint = 25133.75
    current_price = 24750.0 # Reported by user
    
    print(f"\nREFERENCIA MENSUAL (W2 LINE): {midpoint}")
    print(f"PRECIO INFORMADO POR USUARIO: {current_price}")
    
    if current_price < midpoint:
        print("\n⚠️ ALERTA: NQ está COTIZANDO POR DEBAJO del 50% mensual (W2).")
        print("Si el cierre de mañana (Viernes) es < 25,133.75, Febrero se confirma como un MES BAJISTA.")
        print("Esto invalida señales de compra y activa el 'Bear Bias' mensual.")

if __name__ == "__main__":
    check_current_week_detail()
