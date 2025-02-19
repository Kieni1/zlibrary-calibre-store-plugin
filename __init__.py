store_version = 8  # Needed for dynamic plugin loading

__license__ = "GPLv3"
__copyright__ = "tekofx"
__docformat__ = "restructuredtext en"

from calibre.customize import StoreBase


class LibgenStore(StoreBase):
    name = "Z-Library"
    version = (1, 0, 0)
    description = "Searches for books on Z-Library"
    author = "tekofx"
    drm_free_only = True
    actual_plugin = "calibre_plugins.store_zlibrary.zlibrary_plugin:ZLibraryStorePlugin"
    formats = ["EPUB", "PDF"]
