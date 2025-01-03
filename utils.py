def generate_default_dates(data):
    min_date = data['Order_Date'].min()
    max_date = data['Order_Date'].max()
    start_date = min_date.strftime('%Y-%m-%d')
    end_date = max_date.strftime('%Y-%m-%d')

    return start_date, end_date