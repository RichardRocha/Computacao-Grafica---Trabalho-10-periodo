import os
import csv
import matplotlib.pyplot as plt
import numpy as np


def generate_charts(csv_path="results/benchmark_metrics.csv", out_dir="docs/charts"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Arquivo {csv_path} não encontrado. Execute main.py e pressione 'B' primeiro.")

    os.makedirs(out_dir, exist_ok=True)

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    labels_map = {
        "Cenario_1_Frontal_Completa": "Cenário 1\n(Frontal 100%)",
        "Cenario_2_Angulada_Parcial": "Cenário 2\n(Angulada ~35%)",
        "Cenario_3_Interna_Aproximada": "Cenário 3\n(Interna ~12%)",
        "Cenario_4_Terra_Espaco_Vazio": "Cenário 4\n(Terra / Vazio 0%)"
    }

    cenarios = list(labels_map.keys())
    x_labels = [labels_map[c] for c in cenarios]

    fps_off = [float(next(r["fps"] for r in rows if r["cenario"] == c and r["culling"] == "DESLIGADO")) for c in cenarios]
    fps_on = [float(next(r["fps"] for r in rows if r["cenario"] == c and r["culling"] == "LIGADO")) for c in cenarios]

    ms_off = [float(next(r["frame_time_ms"] for r in rows if r["cenario"] == c and r["culling"] == "DESLIGADO")) for c in cenarios]
    ms_on = [float(next(r["frame_time_ms"] for r in rows if r["cenario"] == c and r["culling"] == "LIGADO")) for c in cenarios]

    discard_on = [float(next(r["descarte_pct"] for r in rows if r["cenario"] == c and r["culling"] == "LIGADO")) for c in cenarios]
    polys_on = [int(next(r["triangulos_gpu"] for r in rows if r["cenario"] == c and r["culling"] == "LIGADO")) / 1000.0 for c in cenarios]

    x = np.arange(len(cenarios))
    width = 0.35

    plt.rcParams.update({'font.size': 10, 'font.family': 'sans-serif'})

    # Gráfico 1: Comparativo de FPS
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    rects1 = ax.bar(x - width / 2, fps_off, width, label='Sem Culling (Força Bruta)', color='#d9534f')
    rects2 = ax.bar(x + width / 2, fps_on, width, label='Com View Frustum Culling', color='#2b5c8f')

    ax.set_ylabel('Taxa de Quadros Média (FPS)')
    ax.set_title('Comparativo de Desempenho: FPS Médio por Ângulo de Câmera (RTX 4060)')
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in rects1 + rects2:
        h = rect.get_height()
        ax.annotate(f'{h:.0f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "grafico_fps.png"), dpi=300)
    plt.close()

    # Gráfico 2: Tempo de Quadro (ms)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    rects1 = ax.bar(x - width / 2, ms_off, width, label='Sem Culling (ms)', color='#e67e22')
    rects2 = ax.bar(x + width / 2, ms_on, width, label='Com View Frustum Culling (ms)', color='#27ae60')

    ax.set_ylabel('Tempo de Renderização por Quadro (ms)')
    ax.set_title('Latência de Renderização (Frame Time) - Menor é Melhor')
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in rects1 + rects2:
        h = rect.get_height()
        ax.annotate(f'{h:.2f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "grafico_frametime.png"), dpi=300)
    plt.close()

    # Gráfico 3: Percentual de Descarte e Triângulos na GPU
    fig, ax1 = plt.subplots(figsize=(7.5, 4.2))
    bars = ax1.bar(x, discard_on, width=0.45, color='#34495e', label='Geometria Descartada (%)')
    ax1.set_ylabel('Módulos / Triângulos Descartados (%)', color='#34495e')
    ax1.set_ylim(0, 115)
    ax1.set_xticks(x)
    ax1.set_xticklabels(x_labels)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    for bar, p_k in zip(bars, polys_on):
        h = bar.get_height()
        ax1.annotate(f'{h:.1f}%\n({p_k:.1f}k tri)', xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    ax1.set_title('Eficiência de Redução Geométrica do View Frustum Culling')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "grafico_descarte.png"), dpi=300)
    plt.close()

    print(f"-> Gráficos salvos com sucesso em '{out_dir}/'!")


if __name__ == "__main__":
    generate_charts()