import FixEPub as fep

epf=fep.epub_file('/Users/goios/Downloads/1483lelamvl.epub')
epf.remove_page_numbers()
epf.print_text()
epf.finish()