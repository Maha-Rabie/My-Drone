import matplotlib.pyplot as plt
def show_heatmap(data):
    plt.figure(figsize=(6,6))
    plt.imshow(data,cmap='viridis')
    plt.colorbar(label="Signal Strenth (dBm)")
    plt.title("Tunnel RF Heatmap")

    plt.xlabel("X Position")
    plt.ylabel("Y Position")

    plt.show(block=True)
