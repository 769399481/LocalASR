from PyInstaller.utils.hooks import collect_data_files, copy_metadata
datas = collect_data_files("transformers", include_py_files=True)
for name in ("transformers", "torch", "numpy", "packaging", "huggingface-hub", "tokenizers",
             "safetensors", "regex", "pyyaml", "filelock", "tqdm", "requests", "sentencepiece", "sacremoses"):
    datas += copy_metadata(name)
hiddenimports = ["transformers.models.marian.modeling_marian", "transformers.models.marian.tokenization_marian",
                 "transformers.models.marian.configuration_marian"]
module_collection_mode = "pyz+py"
