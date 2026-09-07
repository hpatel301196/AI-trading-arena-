def generate_order_flow_ai_context(order_flow_data):
    """
    Formats the raw order flow data into a natural language sentence 
    for your AI War Room Prompt.
    """
    delta_status = "Bulls Aggressively Buying" if order_flow_data['delta_volume'] > 0 else "Bears Aggressively Selling"
    
    prompt_snippet = f"""
    [ORDER FLOW & MICROSTRUCTURE]
    • Order Book Imbalance: {order_flow_data['imbalance']} (>1.0 Bullish, <1.0 Bearish)
    • Key Buy Wall (Support): ${order_flow_data['top_buy_wall_price']} ({order_flow_data['top_buy_wall_size']} BTC)
    • Key Sell Wall (Resistance): ${order_flow_data['top_sell_wall_price']} ({order_flow_data['top_sell_wall_size']} BTC)
    • Volume Point of Control (POC): ${order_flow_data['poc_price']}
    • Recent Delta Profile: {order_flow_data['delta_volume']} BTC ({delta_status})
    """
    return prompt_snippet
