"""
Prepara a base de vendas da Porsche para a dashboard.

Entrada : data/porsche_base_sanitizada.xlsx  (aba "Sanitized", 100 vendas)
Saídas  : data/vendas_porsche_tratada.csv     (base limpa, só valores)
          index.html                          (dados embutidos entre os marcadores DATA)

O que o script faz:
  1. Fica só com as colunas *Sanitized* (+ sale_id).
  2. Converte preço, ano do modelo e quilometragem em número.
  3. Remove dados pessoais (customer_name e salesperson) — a base vai embutida no HTML.
  4. Cria a "família" do modelo (911, 718, Cayenne, Macan, Taycan, Panamera).
  5. Agrupa os 10 status de entrega em 3 grupos (Entregue / Em andamento / Cancelada).
  6. Segunda regra para datas INVALID (olhando a data crua):
       - formato AAAA/DD/MM com dia e mês trocados  -> data recuperada
       - dia impossível (30/02, 31/04...) mas ano e mês legíveis -> data parcial (só ano e mês)

Uso:  python scripts/preparar_base.py
"""
from __future__ import annotations

import calendar
import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "porsche_base_sanitizada.xlsx"
SAIDA_CSV = RAIZ / "data" / "vendas_porsche_tratada.csv"
HTML = RAIZ / "index.html"

MESES = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}

STATUS_GRUPO = {
    "Delivered": "Entregue",
    "Cancelled": "Cancelada",
}
STATUS_PT = {
    "Delivered": "Entregue",
    "Pending": "Pendente",
    "In Transit": "Em trânsito",
    "Cancelled": "Cancelada",
    "Awaiting Delivery": "Aguardando entrega",
    "Pending Approval": "Aguardando aprovação",
    "Shipped": "Despachada",
    "Awaiting Pickup": "Aguardando retirada",
    "Pending Review": "Em análise",
    "Awaiting Review": "Em análise",
}
PAGAMENTO_PT = {
    "Wire Transfer": "Transf. internacional",
    "Bank Transfer": "Transferência bancária",
    "Credit Card": "Cartão de crédito",
    "Debit Card": "Cartão de débito",
    "Financing": "Financiamento",
    "Cash": "Dinheiro",
    "Lease": "Leasing",
    "Crypto Payment": "Cripto",
    "ACH Payment": "ACH",
}
FAMILIAS = ["911", "718", "Cayenne", "Macan", "Taycan", "Panamera"]


def familia(modelo: str) -> str:
    for f in FAMILIAS:
        if modelo.startswith(f):
            return f
    return "Outros"


def data_valida(a: int, m: int, d: int) -> bool:
    try:
        date(a, m, d)
        return True
    except ValueError:
        return False


def recuperar_data(crua: str) -> tuple[str | None, int | None, int | None, str]:
    """Tenta extrair algo útil de uma data marcada como INVALID.
    Retorna (data_iso, ano, mes, status)."""
    s = str(crua).strip()

    # AAAA/XX/YY ou AAAA-XX-YY
    m = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", s)
    if m:
        a, x, y = map(int, m.groups())
        if x > 12 and 1 <= y <= 12 and data_valida(a, y, x):  # dia e mês trocados
            return date(a, y, x).isoformat(), a, y, "recuperada"
        if 1 <= x <= 12:
            return None, a, x, "parcial"

    # MM/DD/AAAA
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        mes, _, a = map(int, m.groups())
        if 1 <= mes <= 12:
            return None, a, mes, "parcial"

    # "February 30th, 2026"
    m = re.fullmatch(r"([A-Za-z]+)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+(\d{4})", s)
    if m and m.group(1).lower() in MESES:
        return None, int(m.group(2)), MESES[m.group(1).lower()], "parcial"

    return None, None, None, "invalida"


def main() -> None:
    df = pd.read_excel(ENTRADA, sheet_name="Sanitized", dtype=str)

    linhas = []
    for _, r in df.iterrows():
        bruto = r["SaleDateSanitized"]
        if bruto != "INVALID":
            iso = pd.to_datetime(bruto).date().isoformat()
            ano, mes, st = int(iso[:4]), int(iso[5:7]), "original"
        else:
            iso, ano, mes, st = recuperar_data(r["sale_date"])

        status = r["DeliveryStatusSanitized"]
        linhas.append(
            {
                "id": int(r["sale_id"]),
                "data_venda": iso,
                "ano_venda": ano,
                "mes_venda": mes,
                "qualidade_data": st,
                "modelo": r["PorscheModelSanitized"],
                "familia": familia(r["PorscheModelSanitized"]),
                "ano_modelo": int(r["ModelYearSanitized"]),
                "preco_usd": round(float(r["SalesPriceSanitized"]), 2),
                "milhas": int(float(r["VehicleMileageSanitized"])),
                "pagamento": PAGAMENTO_PT.get(r["PayMethodSanitized"], r["PayMethodSanitized"]),
                "cidade": r["CitySanitized"],
                "estado": r["StateSanitized"],
                "status": STATUS_PT.get(status, status),
                "status_grupo": STATUS_GRUPO.get(status, "Em andamento"),
            }
        )

    base = pd.DataFrame(linhas).sort_values("id")
    base.to_csv(SAIDA_CSV, index=False, encoding="utf-8")

    # Embute no index.html (arquivo único, sem fórmula nem fetch)
    if HTML.exists():
        html = HTML.read_text(encoding="utf-8")
        payload = json.dumps(base.where(base.notna(), None).to_dict("records"), ensure_ascii=False)
        novo, n = re.subn(
            r"/\*DATA_START\*/.*?/\*DATA_END\*/",
            lambda _: f"/*DATA_START*/{payload}/*DATA_END*/",
            html,
            flags=re.S,
        )
        if n != 1:
            raise SystemExit("Marcadores DATA_START/DATA_END não encontrados no index.html")
        HTML.write_text(novo, encoding="utf-8")

    print(f"{len(base)} vendas tratadas -> {SAIDA_CSV.name}")
    print(base["qualidade_data"].value_counts().to_string())


if __name__ == "__main__":
    main()
