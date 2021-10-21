# See
# https://github.com/django-webpack/django-webpack-loader/issues/227

# webpack.py
from webpack_loader.loader import WebpackLoader

class CustomWebpackLoader(WebpackLoader):
    def get_chunk_url(self, chunk):
        asset = self.get_assets()['assets'][chunk['name']]
        return super().get_chunk_url(asset)

    def filter_chunks(self, chunks):
        chunks = [chunk if isinstance(chunk, dict) else {'name': chunk} for chunk in chunks]
        return super().filter_chunks(chunks)

