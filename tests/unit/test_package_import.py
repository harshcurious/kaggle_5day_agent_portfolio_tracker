def test_package_import_smoke():
    import portfolio_tracker

    assert portfolio_tracker.__version__ == "0.1.0"
