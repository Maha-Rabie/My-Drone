# signal_model.py
import math

# Antenna position at the tunnel entrance (Grid coordinates)
TRANSMITTER_POS = (2, 0)  

# Perfect signal strength (dBm) at 1 meter away
P0 = -40                  

# Penalty factor for signal drop caused by tunnel walls
PATH_LOSS_EXPONENT = 2.5  

# Intensity level of environmental radio interference
SHADOW_FADING_STD = 2.0   

def get_signal(x, y):
    """
    Calculates the radio signal strength at any given drone position.
    """
    tx_x, tx_y = TRANSMITTER_POS
    
    # Step 1: Calculate the straight-line distance between the drone and the antenna
    distance = math.sqrt((x - tx_x)**2 + (y - tx_y)**2)
    
    # Safety check: Prevent math errors by ensuring distance is never zero
    if distance < 1:
        distance = 1 
        
    # Step 2: Apply the standard physics formula for signal decay over distance
    path_loss = 10 * PATH_LOSS_EXPONENT * math.log10(distance)
    signal = P0 - path_loss
    
    # Step 3: Add realistic tunnel noise caused by waves bouncing off walls
    noise = (math.sin(x * 5) * math.cos(y * 5)) * SHADOW_FADING_STD
    signal += noise
    
    # Step 4: Keep the output realistic (-120 dBm is total radio silence)
    return round(max(signal, -120.0), 2)