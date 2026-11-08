from pathlib import Path
import json

import numpy as np
import pandas as pd

DATA_DIR = Path("data")

if not DATA_DIR.exists():
    raise FileNotFoundError(
        "Could not find the data/ folder. "
        "Open the project root folder in VS Code, "
        "where app.py and data/ are side by side."
    )

for path in sorted(DATA_DIR.iterdir()):
    print("\n" + "=" * 100)
    print(path.name)

    try:
        if path.suffix == ".parquet":
            dataframe = pd.read_parquet(path)

            print("Shape:", dataframe.shape)

            print("\nColumns:")
            print(dataframe.columns.tolist())

            print("\nDtypes:")
            print(dataframe.dtypes.astype(str).to_dict())

            print("\nFirst two rows:")
            print(
                dataframe.head(2).to_dict(
                    orient="records"
                )
            )

        elif path.suffix == ".json":
            content = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            print("Top-level keys:")
            print(list(content.keys()))

            print("\nJSON preview:")
            print(
                json.dumps(
                    content,
                    indent=2,
                    default=str,
                )[:10000]
            )

        elif path.suffix == ".npz":
            archive = np.load(
                path,
                allow_pickle=True,
            )

            print("Arrays:", archive.files)

            for key in archive.files:
                array = archive[key]

                print(
                    f"{key}: "
                    f"shape={array.shape}, "
                    f"dtype={array.dtype}"
                )

    except Exception as error:
        print("Could not inspect this file:")
        print(repr(error))