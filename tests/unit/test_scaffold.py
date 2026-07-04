import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REQUIRED_DIRS = [
    "voxr",
    "tests/unit",
    "tests/integration",
    "data/icons",
    "packaging",
]

REQUIRED_INIT_FILES = [
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
]


def test_required_directories_exist():
    for d in REQUIRED_DIRS:
        assert os.path.isdir(os.path.join(PROJECT_ROOT, d)), f"Directory missing: {d}"


def test_required_init_files_exist():
    for f in REQUIRED_INIT_FILES:
        assert os.path.isfile(os.path.join(PROJECT_ROOT, f)), f"File missing: {f}"


def test_voxr_package_version():
    import voxr
    assert hasattr(voxr, "__version__"), "voxr.__version__ not defined"
    assert voxr.__version__ == "0.1.0-dev"
