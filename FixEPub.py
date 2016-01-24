import zipfile
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import re
import string

# iterator for all html files

class epub_file:
    def __init__(self,epub_file):
        epub_basename = os.path.splitext(epub_file)[0]
        epub_dirname = os.path.basename(epub_basename)
        destdir = os.path.join(tempfile.gettempdir(),'FixEPub',epub_dirname)
        try:
            os.makedirs(destdir)
        except OSError:
            if os.path.isdir(destdir):
                # if directory exists, clean it
                shutil.rmtree(destdir)
            else:
                raise
        
        self.epub_file = epub_file
        self.new_epub = epub_basename + '_fixed.epub'
        self.epub_tree = destdir
        self.unzip_epub(destdir)
        
        ## Manifest data
        self.content_file='META-INF/container.xml'
        self.content_namespace = '{urn:oasis:names:tc:opendocument:xmlns:container}'
        self.opf_namespace = '{http://www.idpf.org/2007/opf}'
        
        self.opf_file = self.get_content_file()
        
        ## HTML data
        self.html_namespace = '{http://www.w3.org/1999/xhtml}'
    
    
    def unzip_epub(self,dest_dir):
        with zipfile.ZipFile(self.epub_file) as zf:
            zf.extractall(dest_dir)
            
    def zip_epub(self):
        with zipfile.ZipFile(self.new_epub, 'w', zipfile.ZIP_DEFLATED) as zf:
            for dirpath, dirnames, filenames in os.walk(self.epub_tree):
                relpath = os.path.relpath(dirpath,self.epub_tree)
                for file in filenames:
                    src = os.path.join(dirpath,file)
                    dest = os.path.join(relpath,file)
                    zf.write(src,dest)
        zf.close()
        
    def get_content_file(self):
        contxml=ET.parse(os.path.join(self.epub_tree,self.content_file))        
        contfile=contxml.find(".//*"+self.content_namespace+"rootfile").attrib['full-path']
        return contfile
        
    def get_html_iterator(self):
        def html_gen():
            for f in self.get_ordered_html_list():
                filename = os.path.join(self.epub_tree,f)
                yield filename,ET.parse(filename)
        return html_gen()
        
    def get_ordered_html_list(self):
        opf_file = self.get_content_file()
        opfxml = ET.parse(os.path.join(self.epub_tree,opf_file))
        toclist = opfxml.findall(".//*{http://www.idpf.org/2007/opf}itemref")
        htmlfiles = []
        for tocitem in toclist:
            htid = tocitem.attrib['idref']
            html_item = opfxml.find(".//*[@id='"+htid+"']")
            html_file = html_item.attrib['href']
            htmlfiles.append(html_file)
            
        return htmlfiles
            
    def print_text(self):
        it = self.get_html_iterator()
        for htf,xi in it:
            root = xi.getroot()
            ptags=root.findall('.//*'+self.html_namespace+'p')
            for pt in ptags:
                try:
                    if pt.text is not None:
                        print pt.text
                except UnicodeEncodeError as e:
                    print '****' + str(e) 
        
    def strip_html_tags(self, file):
        pass
        
    def remove_page_numbers(self):
        it = self.get_html_iterator()
        taglist = []
        prevnum = 0
        search = './/'+self.html_namespace+'p'
        for htf,xi in it:
            root = xi.getroot()
            parents=root.findall(search+'/..')
            for p in parents:
                for tag in p.findall(search):
                    try:
                        #print tag.text
                        if re.findall('^\s*\d+\s*$', tag.text):
                            thisnum = string.atoi(tag.text)
                            p.remove(tag)
                            if thisnum > prevnum+1:
                                self.remove_intermediate_numbers(prevnum,thisnum,taglist)
                            prevnum = thisnum
                            prevhtml = xi
                            #print 'Removed page number '+str(thisnum)+' from '+htf
                        else:
                            taglist.append(tag)
                    except TypeError as e:
                        #print type(e)
                        #print e.args
                        #print e
                        pass
            xi.write(htf, encoding='utf-8')
        
    def remove_intermediate_numbers(self,prevnum,thisnum,taglist):
        for tag in taglist:
            for num in xrange(prevnum+1,thisnum):
                try:
                    if re.findall('\s*'+str(num)+'\s*', tag.text):
                        tag.text=re.sub('\s*'+str(num)+'\s*','',tag.text)
                        # print 'Erased page number '+str(num)
                    
                except TypeError:
                    pass
        
        
    def finish(self):
        '''Rezip the epub file and cleanup temp dir'''
        self.zip_epub()
        shutil.rmtree(self.epub_tree)


        