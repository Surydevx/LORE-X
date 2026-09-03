import re

class CarbonMetrics:
    CO2_KG_PER_KWH = 0.4
    KG_CO2_PER_TREE_YEAR = 22.0
    
    KWH_RE = re.compile(r"~?\s*([\d,.]+)\s*kWh", re.IGNORECASE)
    COST_RE = re.compile(r"cost|increase|added|more", re.IGNORECASE)

    @classmethod
    def parse_carbon(cls, raw: str) -> tuple[float, float]:
        """
        Return (savings_kwh, cost_kwh) parsed from a Carbon impact string.
        """
        match = cls.KWH_RE.search(raw)
        if not match:
            return 0.0, 0.0
        
        value = float(match.group(1).replace(",", ""))
        
        if cls.COST_RE.search(raw):
            return 0.0, value
        return value, 0.0

    @classmethod
    def calculate_impact(cls, total_savings_kwh: float, total_cost_kwh: float) -> dict[str, float]:
        """
        Calculate carbon impact metrics from kWh values.
        """
        net_kwh = total_savings_kwh - total_cost_kwh
        co2_kg_month = round(net_kwh * cls.CO2_KG_PER_KWH, 1)
        trees_year = round((co2_kg_month * 12) / cls.KG_CO2_PER_TREE_YEAR, 1) if cls.KG_CO2_PER_TREE_YEAR else 0.0
        
        return {
            "net_kwh": net_kwh,
            "co2_kg_month": co2_kg_month,
            "trees_year": trees_year
        }
