import csv
import json
import os
from datetime import datetime
from typing import Dict, List


class ExportManager:
    @staticmethod
    def to_json(data: Dict, filepath: str = None) -> str:
        output = json.dumps(data, indent=2, default=str)
        if filepath:
            with open(filepath, "w") as f:
                f.write(output)
        return output

    @staticmethod
    def to_csv(data: Dict, filepath: str = None) -> str:
        rows = []
        base = {
            "address": data["address"],
            "chain": data["chain"],
            "native_balance": data["native_balance"],
            "transaction_count": data["transaction_count"],
            "scanned_at": datetime.now().isoformat(),
        }

        if data["last_transaction"]:
            lt = data["last_transaction"]
            base["last_tx_hash"] = lt["hash"]
            base["last_tx_value"] = lt["value"]
            base["last_tx_time"] = lt["timestamp"]
        else:
            base.update(
                {
                    "last_tx_hash": "",
                    "last_tx_value": "",
                    "last_tx_time": "",
                }
            )

        if data["top_tokens"]:
            for token in data["top_tokens"]:
                row = {
                    **base,
                    "token_symbol": token["symbol"],
                    "token_contract": token["contract"],
                    "token_volume": token["total_value"],
                    "token_tx_count": token["tx_count"],
                }
                rows.append(row)
        else:
            rows.append(base)

        output_lines = []
        if rows:
            writer_data = rows
            fieldnames = list(writer_data[0].keys())
            output_lines.append(",".join(fieldnames))
            for row in writer_data:
                output_lines.append(
                    ",".join(str(row.get(f, "")) for f in fieldnames)
                )

        output = "\n".join(output_lines)
        if filepath:
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(writer_data)
        return output

    @staticmethod
    def export(data: Dict, fmt: str, filepath: str = None):
        if fmt == "json":
            return ExportManager.to_json(data, filepath)
        elif fmt == "csv":
            return ExportManager.to_csv(data, filepath)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
