import pandas as pd
import re
from datetime import datetime

#python convert_food_data.py vstupni_soubor.csv vystupni_soubor.csv
#python3.11 conversion2.py  xls.csv food_table_converted.csv

def parse_food_table(csv_content):
    # Rozdělení obsahu podle dnů
    day_blocks = re.split(r'([A-Za-zÁ-Žá-ž]+ \d{2}\.\d{2}\.\d{4}): Table 1', csv_content)[1:]

    # Seznam pro ukládání záznamů
    records = []

    # Zpracování každého dne
    for i in range(0, len(day_blocks), 2):
        if i+1 < len(day_blocks):
            date_str = day_blocks[i].strip()
            content = day_blocks[i+1].strip()

            # Převod data do standardního formátu
            try:
                date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                date_formatted = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                # Pokud není možné převést datum, použijeme původní
                date_formatted = date_str

            # Rozdělení obsahu na řádky
            lines = content.split('\n')

            # Identifikace začátku sekce s potravinami
            start_idx = 0
            for idx, line in enumerate(lines):
                if "Název;Čas zápisu;Množství;kcal;Bílkoviny [g];Sacharidy [g]" in line:
                    start_idx = idx + 1
                    break

            # Najdeme poslední řádek potravin před aktivitami
            end_idx = next((idx for idx, line in enumerate(lines[start_idx:], start_idx) if "Aktivity" in line), len(lines))

            # Zpracování jednotlivých sekcí jídel
            current_meal_type = None

            for line_idx in range(start_idx, end_idx):
                line = lines[line_idx].strip()
                if not line:
                    continue

                # Identifikace typu jídla
                meal_match = re.match(r'([A-Za-zÁ-Žá-ž]+ [A-Za-zÁ-Žá-ž]+) \[\d+(?:\.\d+)? kcal\]', line)
                if meal_match:
                    current_meal_type = meal_match.group(1)
                    continue

                # Zpracování řádku s potravinou
                if ';' in line and not line.startswith(';;;;'):
                    fields = line.split(';')
                    food_name = fields[0].strip()

                    # Přeskočíme prázdné řádky a souhrny
                    if not food_name or food_name == "Název" or "celkem" in food_name.lower():
                        continue

                    # Získání času zápisu
                    time_str = fields[1].strip() if len(fields) > 1 and fields[1].strip() else "00:00"

                    # Pokud nejsou data k dispozici, přeskočíme
                    if len(fields) < 8:
                        continue

                    # Vytvoření záznamu s pouze požadovanými údaji
                    record = {
                        "datum": date_formatted,
                        "cas": time_str,
                        "typ_jidla": current_meal_type if current_meal_type else "",
                        "nazev_jidla": food_name,
                        "mnozstvi": fields[2].strip() if len(fields) > 2 else "",
                        "kcal": float(fields[3].replace(',', '.').replace('\xa0', '')) if len(fields) > 3 and fields[3].strip() else 0,
                        "bilkoviny_g": float(fields[4].replace(',', '.')) if len(fields) > 4 and fields[4].strip() else 0,
                        "sacharidy_g": float(fields[5].replace(',', '.')) if len(fields) > 5 and fields[5].strip() else 0,
                        "cukry_g": float(fields[6].replace(',', '.')) if len(fields) > 6 and fields[6].strip() else 0,
                        "tuky_g": float(fields[7].replace(',', '.')) if len(fields) > 7 and fields[7].strip() else 0
                    }

                    # Přidáme nasycené tuky, pokud jsou k dispozici
                    if len(fields) > 8 and fields[8].strip():
                        record["nasycene_mastne_kyseliny_g"] = float(fields[8].replace(',', '.'))

                    records.append(record)

    # Vytvoření DataFramu z záznamů
    if records:
        df = pd.DataFrame(records)

        # Vytvoření sloupce datum_cas pro snadnější řazení
        df['datum_cas'] = pd.to_datetime(df['datum'] + ' ' + df['cas'], errors='coerce')

        # Seřazení podle datumu a času
        df = df.sort_values('datum_cas')

        # Můžeme buď ponechat sloupec datum_cas, nebo ho odstranit
        df = df.drop('datum_cas', axis=1)

        return df
    else:
        return pd.DataFrame()

def convert_to_simple_csv(input_file, output_file):
    """
    Převede komplexní CSV s potravinovými daty na jednodušší formát.

    Args:
        input_file: Cesta k vstupnímu CSV souboru nebo obsah CSV jako řetězec
        output_file: Cesta k výstupnímu CSV souboru

    Returns:
        Pandas DataFrame s převedenými daty
    """
    # Zjistíme, zda je vstup soubor nebo řetězec
    if isinstance(input_file, str) and (input_file.endswith('.csv') or '\n' not in input_file):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return pd.DataFrame()
    else:
        content = input_file

    # Převedeme data
    df = parse_food_table(content)

    # Uložíme výsledek
    if not df.empty and output_file:
        df.to_csv(output_file, index=False, encoding='utf-8')

    return df

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        df = convert_to_simple_csv(input_file, output_file)
        print(f"Data byla převedena do souboru {output_file}")
        print(f"Počet záznamů: {len(df)}")
    else:
        print("Použití: python convert_food_data.py vstupni_soubor.csv vystupni_soubor.csv")