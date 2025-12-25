"""
Tools lõi cho Vietnamese Financial AI Agent
Các hàm wrapper cho VnStock API để LLM có thể gọi
"""

import json
import pandas as pd
from vnstock import Vnstock
from datetime import datetime, timedelta


def get_company_info(ticker: str) -> str:
    """
    Lấy thông tin tổng quan về công ty
    
    Args:
        ticker: Mã chứng khoán (ví dụ: 'FPT', 'VCB', 'HPG')
    
    Returns:
        JSON string chứa thông tin công ty hoặc thông báo lỗi
    """
    try:
        stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
        df = stock.company.overview()
        
        if df is None or df.empty:
            return json.dumps({"error": f"Không tìm thấy thông tin cho mã {ticker}"}, ensure_ascii=False)
        
        # Chuyển DataFrame sang JSON
        result_json = df.to_json(orient='records', force_ascii=False)
        return result_json
        
    except Exception as e:
        return json.dumps({"error": f"Lỗi khi lấy thông tin công ty {ticker}: {str(e)}"}, ensure_ascii=False)


def get_historical_price(ticker: str, start_date: str, end_date: str) -> str:
    """
    Lấy giá lịch sử của cổ phiếu
    
    Args:
        ticker: Mã chứng khoán (ví dụ: 'FPT', 'VCB', 'HPG')
        start_date: Ngày bắt đầu (định dạng 'YYYY-MM-DD')
        end_date: Ngày kết thúc (định dạng 'YYYY-MM-DD')
    
    Returns:
        JSON string chứa dữ liệu giá lịch sử hoặc thông báo lỗi
    """
    try:
        stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
        df = stock.quote.history(start=start_date, end=end_date)
        
        if df is None or df.empty:
            return json.dumps({"error": f"Không có dữ liệu giá cho mã {ticker} trong khoảng thời gian này"}, ensure_ascii=False)
        
        # Chuyển DataFrame sang JSON
        result_json = df.to_json(orient='records', force_ascii=False)
        return result_json
        
    except Exception as e:
        return json.dumps({"error": f"Lỗi khi lấy giá lịch sử {ticker}: {str(e)}"}, ensure_ascii=False)


def calculate_technical_indicator(ticker: str, indicator_name: str, window_size: int, start_date: str, end_date: str) -> str:
    """
    Tính các chỉ báo kỹ thuật (SMA, RSI) cho cổ phiếu
    
    Args:
        ticker: Mã chứng khoán (ví dụ: 'FPT', 'VCB', 'HPG')
        indicator_name: Tên chỉ báo ('SMA' hoặc 'RSI')
        window_size: Độ dài chu kỳ (ví dụ: 14, 20, 50)
        start_date: Ngày bắt đầu (định dạng 'YYYY-MM-DD')
        end_date: Ngày kết thúc (định dạng 'YYYY-MM-DD')
    
    Returns:
        Chuỗi mô tả kết quả hoặc thông báo lỗi
    """
    try:
        # Lấy dữ liệu giá lịch sử
        price_data_json = get_historical_price(ticker, start_date, end_date)
        
        # Parse JSON thành DataFrame
        price_data = json.loads(price_data_json)
        
        # Kiểm tra nếu có lỗi
        if isinstance(price_data, dict) and "error" in price_data:
            return json.dumps(price_data, ensure_ascii=False)
        
        # Chuyển về DataFrame
        df = pd.DataFrame(price_data)
        
        if df.empty:
            return json.dumps({"error": f"Không có dữ liệu để tính {indicator_name}"}, ensure_ascii=False)
        
        # Đảm bảo cột 'close' tồn tại
        if 'close' not in df.columns:
            return json.dumps({"error": "Dữ liệu không có cột 'close'"}, ensure_ascii=False)
        
        # Tính chỉ báo kỹ thuật
        indicator_name_upper = indicator_name.upper()
        
        if indicator_name_upper == 'SMA':
            # Tính Simple Moving Average
            df[f'SMA_{window_size}'] = df['close'].rolling(window=window_size).mean()
            latest_value = df[f'SMA_{window_size}'].iloc[-1]
            
            if pd.isna(latest_value):
                return f"Không đủ dữ liệu để tính SMA {window_size} ngày cho {ticker.upper()}"
            
            return f"Chỉ số SMA {window_size} ngày của {ticker.upper()} là {latest_value:.2f}"
        
        elif indicator_name_upper == 'RSI':
            # Tính Relative Strength Index
            # RSI = 100 - (100 / (1 + RS))
            # RS = Average Gain / Average Loss
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window_size).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window_size).mean()
            
            rs = gain / loss
            df[f'RSI_{window_size}'] = 100 - (100 / (1 + rs))
            latest_value = df[f'RSI_{window_size}'].iloc[-1]
            
            if pd.isna(latest_value):
                return f"Không đủ dữ liệu để tính RSI {window_size} ngày cho {ticker.upper()}"
            
            return f"Chỉ số RSI {window_size} ngày của {ticker.upper()} là {latest_value:.2f}"
        
        else:
            return json.dumps({"error": f"Chỉ báo '{indicator_name}' không được hỗ trợ. Chỉ hỗ trợ 'SMA' và 'RSI'"}, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({"error": f"Lỗi khi tính chỉ báo {indicator_name}: {str(e)}"}, ensure_ascii=False)


# Hàm tiện ích để test
if __name__ == "__main__":
    print("Test Tool 1: Thông tin công ty")
    print("=" * 50)
    result1 = get_company_info('FPT')
    print(result1[:200] + "...")
    
    print("\n\nTest Tool 2: Giá lịch sử")
    print("=" * 50)
    result2 = get_historical_price('VCB', '2024-10-01', '2024-11-01')
    print(result2[:200] + "...")
    
    print("\n\nTest Tool 3: RSI")
    print("=" * 50)
    result3 = calculate_technical_indicator('HPG', 'RSI', 14, '2024-09-01', '2024-11-01')
    print(result3)
    
    print("\n\nTest Tool 3: SMA")
    print("=" * 50)
    result4 = calculate_technical_indicator('FPT', 'SMA', 20, '2024-09-01', '2024-11-01')
    print(result4)
