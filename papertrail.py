"""
PaperTrail - Desktop Application
A local citation management tool supporting multiple citation styles
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import Dict, List, Optional
import os

# Database setup
class CitationDatabase:
    def __init__(self, db_path="citations.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with citations table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year TEXT,
                journal TEXT,
                volume TEXT,
                issue TEXT,
                pages TEXT,
                doi TEXT,
                url TEXT,
                source_type TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_citation(self, citation_data: Dict) -> int:
        """Add a new citation to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO citations (title, authors, year, journal, volume, issue, pages, doi, url, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            citation_data.get('title', ''),
            citation_data.get('authors', ''),
            citation_data.get('year', ''),
            citation_data.get('journal', ''),
            citation_data.get('volume', ''),
            citation_data.get('issue', ''),
            citation_data.get('pages', ''),
            citation_data.get('doi', ''),
            citation_data.get('url', ''),
            citation_data.get('source_type', 'website')
        ))
        citation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return citation_id
    
    def get_all_citations(self) -> List[Dict]:
        """Retrieve all citations from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM citations ORDER BY id')
        rows = cursor.fetchall()
        conn.close()
        
        citations = []
        for row in rows:
            citations.append({
                'id': row[0],
                'title': row[1],
                'authors': row[2],
                'year': row[3],
                'journal': row[4],
                'volume': row[5],
                'issue': row[6],
                'pages': row[7],
                'doi': row[8],
                'url': row[9],
                'source_type': row[10],
                'date_added': row[11]
            })
        return citations
    
    def delete_citation(self, citation_id: int):
        """Delete a citation by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM citations WHERE id = ?', (citation_id,))
        conn.commit()
        conn.close()
    
    def clear_all(self):
        """Clear all citations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM citations')
        conn.commit()
        conn.close()


# Metadata extraction from URLs
class MetadataExtractor:
    @staticmethod
    def extract_from_url(url: str) -> Dict:
        """Extract metadata from a given URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            metadata = {
                'url': url,
                'title': MetadataExtractor._extract_title(soup),
                'authors': MetadataExtractor._extract_authors(soup),
                'year': MetadataExtractor._extract_year(soup, response.text),
                'journal': MetadataExtractor._extract_journal(soup),
                'doi': MetadataExtractor._extract_doi(soup, response.text),
                'source_type': 'website'
            }
            
            return metadata
            
        except Exception as e:
            raise Exception(f"Failed to extract metadata: {str(e)}")
    
    @staticmethod
    def _extract_title(soup) -> str:
        """Extract title from HTML"""
        # Try meta tags first
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content']
        
        meta_title = soup.find('meta', attrs={'name': 'citation_title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content']
        
        # Fallback to title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        return "Unknown Title"
    
    @staticmethod
    def _extract_authors(soup) -> str:
        """Extract authors from HTML"""
        # Try citation meta tags
        authors = []
        author_tags = soup.find_all('meta', attrs={'name': 'citation_author'})
        for tag in author_tags:
            if tag.get('content'):
                authors.append(tag['content'])
        
        if authors:
            return ', '.join(authors)
        
        # Try other common meta tags
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content']
        
        return ""
    
    @staticmethod
    def _extract_year(soup, html_text) -> str:
        """Extract publication year"""
        # Try citation date meta tag
        date_tag = soup.find('meta', attrs={'name': 'citation_publication_date'})
        if date_tag and date_tag.get('content'):
            year_match = re.search(r'20\d{2}|19\d{2}', date_tag['content'])
            if year_match:
                return year_match.group()
        
        # Try to find year in text
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', html_text)
        if year_match:
            return year_match.group()
        
        return str(datetime.now().year)
    
    @staticmethod
    def _extract_journal(soup) -> str:
        """Extract journal name"""
        journal_tag = soup.find('meta', attrs={'name': 'citation_journal_title'})
        if journal_tag and journal_tag.get('content'):
            return journal_tag['content']
        return ""
    
    @staticmethod
    def _extract_doi(soup, html_text) -> str:
        """Extract DOI"""
        doi_tag = soup.find('meta', attrs={'name': 'citation_doi'})
        if doi_tag and doi_tag.get('content'):
            return doi_tag['content']
        
        # Try to find DOI in text
        doi_match = re.search(r'10\.\d{4,}/[^\s]+', html_text)
        if doi_match:
            return doi_match.group()
        
        return ""


# Citation formatters for different styles
class VancouverFormatter:
    @staticmethod
    def format_citation(citation: Dict, index: int) -> str:
        """Format citation in Vancouver style"""
        parts = []
        
        # Authors (surname initials)
        if citation.get('authors'):
            authors = citation['authors'].split(',')
            formatted_authors = []
            for author in authors[:6]:  # Vancouver limits to 6 authors
                author = author.strip()
                # Simple formatting: assume "First Last" format
                name_parts = author.split()
                if len(name_parts) >= 2:
                    surname = name_parts[-1]
                    initials = ''.join([n[0].upper() for n in name_parts[:-1]])
                    formatted_authors.append(f"{surname} {initials}")
                else:
                    formatted_authors.append(author)
            
            if len(authors) > 6:
                parts.append(', '.join(formatted_authors) + ', et al.')
            else:
                parts.append(', '.join(formatted_authors) + '.')
        
        # Title
        if citation.get('title'):
            parts.append(citation['title'] + '.')
        
        # Journal
        if citation.get('journal'):
            journal_part = citation['journal']
            if citation.get('year'):
                journal_part += f" {citation['year']}"
            if citation.get('volume'):
                journal_part += f";{citation['volume']}"
            if citation.get('issue'):
                journal_part += f"({citation['issue']})"
            if citation.get('pages'):
                journal_part += f":{citation['pages']}"
            parts.append(journal_part + '.')
        elif citation.get('year'):
            parts.append(citation['year'] + '.')
        
        # URL or DOI
        if citation.get('doi'):
            parts.append(f"doi:{citation['doi']}")
        elif citation.get('url'):
            parts.append(f"Available from: {citation['url']}")
        
        return f"{index}. " + ' '.join(parts)


class APAFormatter:
    @staticmethod
    def format_citation(citation: Dict, index: int) -> str:
        """Format citation in APA style"""
        parts = []
        
        # Authors (Last, F. M.)
        if citation.get('authors'):
            authors = citation['authors'].split(',')
            formatted_authors = []
            for author in authors[:20]:  # APA includes up to 20 authors
                author = author.strip()
                name_parts = author.split()
                if len(name_parts) >= 2:
                    surname = name_parts[-1]
                    initials = '. '.join([n[0].upper() for n in name_parts[:-1]]) + '.'
                    formatted_authors.append(f"{surname}, {initials}")
                else:
                    formatted_authors.append(author)
            
            if len(authors) > 20:
                parts.append(', '.join(formatted_authors[:19]) + ', ... ' + formatted_authors[-1])
            elif len(formatted_authors) > 1:
                parts.append(', '.join(formatted_authors[:-1]) + ', & ' + formatted_authors[-1])
            else:
                parts.append(formatted_authors[0])
        
        # Year
        if citation.get('year'):
            parts.append(f"({citation['year']}).")
        
        # Title (sentence case)
        if citation.get('title'):
            parts.append(citation['title'] + '.')
        
        # Journal info (italicized journal name in actual output)
        if citation.get('journal'):
            journal_part = citation['journal']
            if citation.get('volume'):
                journal_part += f", {citation['volume']}"
            if citation.get('issue'):
                journal_part += f"({citation['issue']})"
            if citation.get('pages'):
                journal_part += f", {citation['pages']}"
            parts.append(journal_part + '.')
        
        # DOI or URL
        if citation.get('doi'):
            parts.append(f"https://doi.org/{citation['doi']}")
        elif citation.get('url'):
            parts.append(citation['url'])
        
        return ' '.join(parts)


class MLAFormatter:
    @staticmethod
    def format_citation(citation: Dict, index: int) -> str:
        """Format citation in MLA style"""
        parts = []
        
        # Authors (Last, First)
        if citation.get('authors'):
            authors = citation['authors'].split(',')
            if len(authors) > 0:
                # First author: Last, First
                first_author = authors[0].strip()
                name_parts = first_author.split()
                if len(name_parts) >= 2:
                    parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}.")
                else:
                    parts.append(first_author + '.')
                
                # Additional authors
                if len(authors) > 1:
                    parts[-1] = parts[-1].rstrip('.') + ', et al.'
        
        # Title (in quotes)
        if citation.get('title'):
            parts.append(f'"{citation["title"]}."')
        
        # Journal (italicized in actual output)
        if citation.get('journal'):
            journal_part = citation['journal']
            if citation.get('volume'):
                journal_part += f", vol. {citation['volume']}"
            if citation.get('issue'):
                journal_part += f", no. {citation['issue']}"
            if citation.get('year'):
                journal_part += f", {citation['year']}"
            if citation.get('pages'):
                journal_part += f", pp. {citation['pages']}"
            parts.append(journal_part + '.')
        elif citation.get('year'):
            parts.append(citation['year'] + '.')
        
        # URL or DOI
        if citation.get('doi'):
            parts.append(f"doi:{citation['doi']}.")
        elif citation.get('url'):
            parts.append(citation['url'] + '.')
        
        return ' '.join(parts)


# Main Application GUI
class CitationManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PaperTrail - Citation Manager")
        self.root.geometry("900x700")
        
        self.db = CitationDatabase()
        
        self.formatters = {
            'Vancouver': VancouverFormatter,
            'APA': APAFormatter,
            'MLA': MLAFormatter
        }
        
        self.setup_ui()
        self.refresh_citation_list()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # URL Input Section
        url_frame = ttk.LabelFrame(main_frame, text="Add Citation from URL", padding="10")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(url_frame, text="Fetch & Add", command=self.fetch_and_add).grid(row=0, column=2)
        
        # Manual Entry Section
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Entry", padding="10")
        manual_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        manual_frame.columnconfigure(1, weight=1)
        
        # Manual entry fields
        fields = [
            ('Title:', 'title_entry'),
            ('Authors:', 'authors_entry'),
            ('Year:', 'year_entry'),
            ('Journal:', 'journal_entry'),
            ('DOI:', 'doi_entry')
        ]
        
        for idx, (label, attr) in enumerate(fields):
            ttk.Label(manual_frame, text=label).grid(row=idx, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            entry = ttk.Entry(manual_frame)
            entry.grid(row=idx, column=1, sticky=(tk.W, tk.E), pady=2)
            setattr(self, attr, entry)
        
        ttk.Button(manual_frame, text="Add Citation", command=self.add_manual_citation).grid(row=len(fields), column=0, columnspan=2, pady=(5, 0))
        
        # Citation List Section
        list_frame = ttk.LabelFrame(main_frame, text="Your Citations", padding="10")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create Treeview for citations
        columns = ('ID', 'Title', 'Authors', 'Year')
        self.citation_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.citation_tree.heading(col, text=col)
            if col == 'ID':
                self.citation_tree.column(col, width=50)
            elif col == 'Year':
                self.citation_tree.column(col, width=80)
            else:
                self.citation_tree.column(col, width=200)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.citation_tree.yview)
        self.citation_tree.configure(yscroll=scrollbar.set)
        
        self.citation_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons for list management
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_citation_list).pack(side=tk.LEFT, padx=2)
        
        # Export Section
        export_frame = ttk.LabelFrame(main_frame, text="Export Bibliography", padding="10")
        export_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        style_label = ttk.Label(export_frame, text="Citation Style:")
        style_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.style_var = tk.StringVar(value='Vancouver')
        style_dropdown = ttk.Combobox(export_frame, textvariable=self.style_var, 
                                     values=list(self.formatters.keys()), 
                                     state='readonly', width=15)
        style_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(export_frame, text="Preview", command=self.preview_bibliography).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="Export to File", command=self.export_bibliography).pack(side=tk.LEFT, padx=2)
        
        # Preview Section
        preview_frame = ttk.LabelFrame(main_frame, text="Bibliography Preview", padding="10")
        preview_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, height=10)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def fetch_and_add(self):
        """Fetch metadata from URL and add to database"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a URL")
            return
        
        try:
            # Show loading message
            self.url_entry.config(state='disabled')
            self.root.update()
            
            metadata = MetadataExtractor.extract_from_url(url)
            citation_id = self.db.add_citation(metadata)
            
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(state='normal')
            self.refresh_citation_list()
            messagebox.showinfo("Success", f"Citation added successfully!\nTitle: {metadata.get('title', 'Unknown')}")
            
        except Exception as e:
            self.url_entry.config(state='normal')
            messagebox.showerror("Error", f"Failed to fetch metadata:\n{str(e)}")
    
    def add_manual_citation(self):
        """Add citation from manual entry fields"""
        citation_data = {
            'title': self.title_entry.get().strip(),
            'authors': self.authors_entry.get().strip(),
            'year': self.year_entry.get().strip(),
            'journal': self.journal_entry.get().strip(),
            'doi': self.doi_entry.get().strip(),
            'source_type': 'manual'
        }
        
        if not citation_data['title']:
            messagebox.showwarning("Input Required", "Please enter at least a title")
            return
        
        self.db.add_citation(citation_data)
        
        # Clear fields
        for attr in ['title_entry', 'authors_entry', 'year_entry', 'journal_entry', 'doi_entry']:
            getattr(self, attr).delete(0, tk.END)
        
        self.refresh_citation_list()
        messagebox.showinfo("Success", "Citation added successfully!")
    
    def refresh_citation_list(self):
        """Refresh the citation list display"""
        # Clear existing items
        for item in self.citation_tree.get_children():
            self.citation_tree.delete(item)
        
        # Load citations from database
        citations = self.db.get_all_citations()
        for citation in citations:
            self.citation_tree.insert('', tk.END, values=(
                citation['id'],
                citation['title'][:50] + '...' if len(citation['title']) > 50 else citation['title'],
                citation['authors'][:30] + '...' if citation['authors'] and len(citation['authors']) > 30 else citation['authors'],
                citation['year']
            ))
    
    def delete_selected(self):
        """Delete selected citation"""
        selected = self.citation_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a citation to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected citation?"):
            for item in selected:
                values = self.citation_tree.item(item, 'values')
                citation_id = values[0]
                self.db.delete_citation(int(citation_id))
            
            self.refresh_citation_list()
            messagebox.showinfo("Success", "Citation(s) deleted successfully!")
    
    def clear_all(self):
        """Clear all citations"""
        if messagebox.askyesno("Confirm Clear All", "Are you sure you want to delete ALL citations? This cannot be undone!"):
            self.db.clear_all()
            self.refresh_citation_list()
            self.preview_text.delete(1.0, tk.END)
            messagebox.showinfo("Success", "All citations cleared!")
    
    def preview_bibliography(self):
        """Preview formatted bibliography"""
        citations = self.db.get_all_citations()
        if not citations:
            messagebox.showinfo("No Citations", "No citations to preview. Add some citations first!")
            return
        
        style = self.style_var.get()
        formatter = self.formatters[style]
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, f"Bibliography ({style} Style)\n")
        self.preview_text.insert(tk.END, "=" * 80 + "\n\n")
        
        for idx, citation in enumerate(citations, 1):
            formatted = formatter.format_citation(citation, idx)
            self.preview_text.insert(tk.END, formatted + "\n\n")
    
    def export_bibliography(self):
        """Export bibliography to file"""
        citations = self.db.get_all_citations()
        if not citations:
            messagebox.showinfo("No Citations", "No citations to export. Add some citations first!")
            return
        
        style = self.style_var.get()
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"bibliography_{style.lower()}.txt"
        )
        
        if not filename:
            return
        
        formatter = self.formatters[style]
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Bibliography ({style} Style)\n")
                f.write("=" * 80 + "\n\n")
                
                for idx, citation in enumerate(citations, 1):
                    formatted = formatter.format_citation(citation, idx)
                    f.write(formatted + "\n\n")
            
            messagebox.showinfo("Success", f"Bibliography exported to:\n{filename}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export bibliography:\n{str(e)}")


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = CitationManagerApp(root)
    root.mainloop()
