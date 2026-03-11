import os
import yaml
from typing import Dict, Any

class SemanticLayerLoader:
    def __init__(self, directory: str = "dvd_slackbot/semantic_layer"):
        self.directory = directory
        self.data: Dict[str, Any] = {
            "metrics": {},
            "policies": {},
            "tables": {},
            "views": {},
            "relationships": {}
        }
        self.load_all()

    def load_all(self):
        if not os.path.exists(self.directory):
            return

        for filename in os.listdir(self.directory):
            if filename.endswith((".yaml", ".yml")):
                with open(os.path.join(self.directory, filename), "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    if not content:
                        continue
                        
                    if "metrics" in content:
                        self.data["metrics"].update(content["metrics"])
                    if "policies" in content:
                        self.data["policies"].update(content["policies"])
                    if "tables" in content:
                        self.data["tables"].update(content["tables"])
                    if "views" in content:
                        self.data["views"].update(content["views"])
                    if "relationships" in content:
                        rels = content["relationships"]
                        if isinstance(rels, list):
                            for rel in rels:
                                key = rel.get("name", f"{rel.get('from')}_to_{rel.get('to')}")
                                self.data["relationships"][key] = rel
                        elif isinstance(rels, dict):
                            self.data["relationships"].update(rels)

    def get_metric(self, name: str) -> Dict[str, Any]:
        return self.data["metrics"].get(name, {})

    def get_table_context(self, name: str) -> Dict[str, Any]:
        return self.data["tables"].get(name, {}) or self.data["views"].get(name, {})
        
    def get_join_path(self, table1: str, table2: str) -> Dict[str, Any]:
        return self.data["relationships"].get(f"{table1}_to_{table2}", {}) or self.data["relationships"].get(f"{table2}_to_{table1}", {})

    def get_policies(self) -> Dict[str, Any]:
        return self.data["policies"]
