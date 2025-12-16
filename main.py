# app_stock_inwi.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import mysql.connector
import os

# -----------------------
# Configuration & Thème Inwi
# -----------------------
INWI_PURPLE = "#911B96"
INWI_DARK_PURPLE = "#6D0F66"
INWI_LIGHT = "#F3E5F5"
BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#333333"

# Couleurs d'alerte
ALERT_LOW_STOCK = "#FFCDD2" # Rouge clair
ALERT_BROKEN = "#E0E0E0"    # Gris

FONT_TITLE = ("Helvetica", 20, "bold")
FONT_LABEL = ("Helvetica", 11)
FONT_BUTTON = ("Helvetica", 10, "bold")

# -----------------------
# Connexion MySQL
# -----------------------
def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # mettre votre mot de passe
            database="stock_inwi"
        )
    except mysql.connector.Error:
        return None

# -----------------------
# Gestion Schéma BDD
# -----------------------
def create_tables():
    db = connect_db()
    if db:
        cursor = db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nom VARCHAR(255),
            type VARCHAR(255),
            quantite INT,
            fournisseur VARCHAR(255),
            remarque TEXT,
            statut VARCHAR(50) DEFAULT 'Fonctionnel'
        )
        """)
        # Migration : Ajout colonne statut si elle manque (pour les bdd existantes)
        try:
            cursor.execute("SELECT statut FROM equipements LIMIT 1")
            cursor.fetchall() # IMPORTANT: Consommer le résultat
        except mysql.connector.Error:
            print("Migration: Ajout de la colonne statut...")
            cursor.execute("ALTER TABLE equipements ADD COLUMN statut VARCHAR(50) DEFAULT 'Fonctionnel'")
        
        db.commit()
        db.close()

# -----------------------
# Import Excel
# -----------------------
def import_excel():
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if not file_path:
        return
    try:
        df = pd.read_excel(file_path)
        csv_path = os.path.splitext(file_path)[0] + ".csv"
        df.to_csv(csv_path, index=False)
        messagebox.showinfo("Succès", f"Fichier converti en CSV : {csv_path}")
        update_stock(df)
    except Exception as e:
        messagebox.showerror("Erreur", str(e))

def update_stock(df):
    db = connect_db()
    if not db:
        messagebox.showerror("Erreur", "Impossible de se connecter à la base de données.")
        return
    
    broken_items_alert = [] # Liste pour stocker les péripériques en panne détectés lors de l'import

    try:
        cursor = db.cursor()
        for index, row in df.iterrows():
            nom = row['nom']
            type_eq = row['type']
            quantite = int(row['quantite'])
            fournisseur = row.get('fournisseur', '')
            remarque = row.get('remarque', '')
            
            # Normalisation du statut depuis Excel
            raw_statut = str(row.get('statut', '')).strip().lower()
            if raw_statut in ['en panne', 'hs', 'non fonctionnel', 'broken', 'defective']:
                statut = "En Panne"
            elif raw_statut in ['maintenance', 'en maintenance']:
                statut = "Maintenance"
            else:
                statut = "Fonctionnel"

            # Si c'est en panne, on l'ajoute à la liste d'alerte
            if statut == "En Panne":
                broken_items_alert.append(f"- {nom} ({type_eq})")

            # Logique de mise à jour intelligente
            cursor.execute("SELECT id, quantite, statut FROM equipements WHERE nom=%s AND type=%s", (nom, type_eq))
            results = cursor.fetchall()
            
            if results:
                match_found = False
                for res in results:
                    db_id, db_qte, db_statut = res
                    if db_statut == statut:
                        # Exact match : on ajoute la quantité
                        nouvelle_qte = db_qte + quantite
                        cursor.execute("UPDATE equipements SET quantite=%s WHERE id=%s", (nouvelle_qte, db_id))
                        match_found = True
                        break
                
                if not match_found:
                    # Pas de match exact sur le statut -> Insert d'une nouvelle ligne
                    cursor.execute("""
                    INSERT INTO equipements (nom, type, quantite, fournisseur, remarque, statut) 
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """, (nom, type_eq, quantite, fournisseur, remarque, statut))
            else:
                # N'existe pas du tout -> Insert
                cursor.execute("""
                INSERT INTO equipements (nom, type, quantite, fournisseur, remarque, statut) 
                VALUES (%s,%s,%s,%s,%s,%s)
                """, (nom, type_eq, quantite, fournisseur, remarque, statut))

        db.commit()
        refresh_tree()
        
        # Message final avec Alerte
        msg = "Le stock a été mis à jour."
        if broken_items_alert:
            alert_text = "\n".join(broken_items_alert[:10])
            if len(broken_items_alert) > 10:
                alert_text += "\n... et d'autres."
            messagebox.showwarning("⚠️ ALERTE PÉRIPHÉRIQUES EN PANNE", 
                                   f"Attention, des équipements en panne ont été importés :\n\n{alert_text}\n\nIls ont été enregistrés avec le statut 'En Panne'.")
        else:
            messagebox.showinfo("Import Terminé", msg)

    except Exception as e:
        messagebox.showerror("Erreur SQL", str(e))
    finally:
        db.close()

# -----------------------
# CRUD
# -----------------------
def get_form_data():
    return (entry_nom.get(), entry_type.get(), entry_quantite.get(), 
            entry_fournisseur.get(), entry_remarque.get(), combo_statut.get())

def add_item():
    nom, type_eq, quantite, fournisseur, remarque, statut = get_form_data()
    if not nom or not quantite:
        messagebox.showwarning("Attention", "Nom et Quantité requis")
        return
    
    db = connect_db()
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT quantite FROM equipements WHERE nom=%s AND type=%s AND statut=%s", (nom, type_eq, statut))
        result = cursor.fetchone()
        if result:
            nouvelle_quantite = result[0] + int(quantite)
            cursor.execute("UPDATE equipements SET quantite=%s WHERE nom=%s AND type=%s AND statut=%s",
                           (nouvelle_quantite, nom, type_eq, statut))
        else:
            cursor.execute("""
            INSERT INTO equipements (nom, type, quantite, fournisseur, remarque, statut)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (nom, type_eq, int(quantite), fournisseur, remarque, statut))
        db.commit()
        db.close()
        clear_entries()
        refresh_tree()

def delete_item():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Sélection", "Veuillez sélectionner une ligne.")
        return
    
    confirm = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer cet équipement ?")
    if not confirm:
        return

    values = tree.item(selected, 'values')
    db = connect_db()
    if db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM equipements WHERE id=%s", (values[0],))
        db.commit()
        db.close()
        refresh_tree()

def update_item():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Sélection", "Veuillez sélectionner une ligne à modifier.")
        return
    
    values = tree.item(selected, 'values')
    nom, type_eq, quantite, fournisseur, remarque, statut = get_form_data()
    
    db = connect_db()
    if db:
        cursor = db.cursor()
        cursor.execute("""
        UPDATE equipements
        SET nom=%s, type=%s, quantite=%s, fournisseur=%s, remarque=%s, statut=%s
        WHERE id=%s
        """, (nom, type_eq, int(quantite), fournisseur, remarque, statut, values[0]))
        db.commit()
        db.close()
        clear_entries()
        refresh_tree()

# -----------------------
# Logique Affichage & Notification
# -----------------------
def refresh_tree():
    for i in tree.get_children():
        tree.delete(i)
    
    low_stock_count = 0
    panne_count = 0 
    
    db = connect_db()
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM equipements")
        for row in cursor.fetchall():
            # row: id, nom, type, quantite, fournisseur, remarque, statut
            qte = row[3]
            statut = row[6]
            
            tags = []
            if statut == "En Panne":
                tags.append("panne")
                panne_count += 1
            elif statut == "Maintenance":
                tags.append("panne") # Même couleur visuelle
            elif qte < 5:
                tags.append("low_stock")
                low_stock_count += 1
                
            tree.insert('', 'end', values=row, tags=tuple(tags))
        db.close()
        
    # Notification combinée
    notif_text = "✅ Stock & État OK"
    notif_color = "green"
    
    alerts = []
    if low_stock_count > 0:
        alerts.append(f"{low_stock_count} Faible Stock")
    if panne_count > 0:
        alerts.append(f"{panne_count} En Panne")
        
    if alerts:
        notif_text = "⚠️ " + " | ".join(alerts)
        notif_color = "red"
        
    lbl_notif.config(text=notif_text, foreground=notif_color)

def select_item(event):
    selected = tree.focus()
    if selected:
        values = tree.item(selected, 'values')
        entry_nom.delete(0, tk.END)
        entry_nom.insert(0, values[1])
        entry_type.delete(0, tk.END)
        entry_type.insert(0, values[2])
        entry_quantite.delete(0, tk.END)
        entry_quantite.insert(0, values[3])
        entry_fournisseur.delete(0, tk.END)
        entry_fournisseur.insert(0, values[4])
        entry_remarque.delete(0, tk.END)
        entry_remarque.insert(0, values[5])
        combo_statut.set(values[6])

def clear_entries():
    entry_nom.delete(0, tk.END)
    entry_type.delete(0, tk.END)
    entry_quantite.delete(0, tk.END)
    entry_fournisseur.delete(0, tk.END)
    entry_remarque.delete(0, tk.END)
    combo_statut.set("Fonctionnel")

def show_low_stock_details():
    # Affiche Stocks Faibles ET Pannes
    for i in tree.get_children():
        tree.delete(i)
    db = connect_db()
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM equipements WHERE quantite < 5 OR statut='En Panne'")
        for row in cursor.fetchall():
            statut = row[6]
            tag = 'panne' if statut == 'En Panne' else 'low_stock'
            tree.insert('', 'end', values=row, tags=(tag,))
        db.close()

# -----------------------
# Interface Graphique
# -----------------------
root = tk.Tk()
root.title("Gestion de Stock - Inwi")
root.geometry("1100x700")
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use('clam')
style.configure("TFrame", background=BG_COLOR)
style.configure("TLabelframe", background=BG_COLOR, foreground=INWI_PURPLE)
style.configure("TLabelframe.Label", font=("Helvetica", 12, "bold"), background=BG_COLOR, foreground=INWI_PURPLE)
style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=FONT_LABEL)
style.configure("TButton", font=FONT_BUTTON, background=INWI_PURPLE, foreground="white", borderwidth=0)
style.map("TButton", background=[('active', INWI_DARK_PURPLE)], foreground=[('active', 'white')])

# Header
header_frame = tk.Frame(root, bg=INWI_PURPLE, height=80)
header_frame.pack(fill=tk.X)
tk.Label(header_frame, text="GESTION DE STOCK INWI", font=FONT_TITLE, bg=INWI_PURPLE, fg="white").pack(side=tk.LEFT, padx=20, pady=20)

# Zone Notification
frame_notif = tk.Frame(header_frame, bg=INWI_PURPLE)
frame_notif.pack(side=tk.RIGHT, padx=20, pady=20)
lbl_notif = tk.Label(frame_notif, text="Analyse...", font=("Helvetica", 11, "bold"), bg="white", fg=INWI_PURPLE, padx=10, pady=5)
lbl_notif.pack(side=tk.LEFT, padx=10)
btn_show_alert = tk.Button(frame_notif, text="Voir Alertes", bg="white", fg="red", font=("Helvetica", 10, "bold"), command=show_low_stock_details)
btn_show_alert.pack(side=tk.LEFT)
btn_reset = tk.Button(frame_notif, text="Tout Voir", bg="white", fg="black", font=("Helvetica", 10), command=refresh_tree)
btn_reset.pack(side=tk.LEFT, padx=5)


# Main Layout
main_container = ttk.Frame(root, padding="20")
main_container.pack(fill=tk.BOTH, expand=True)

# Gauche : Formulaire
left_panel = ttk.LabelFrame(main_container, text="Gestion Équipement", padding="20")
left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

ttk.Label(left_panel, text="Statut").pack(anchor="w", pady=(5,0))
combo_statut = ttk.Combobox(left_panel, values=["Fonctionnel", "En Panne", "Maintenance"], state="readonly")
combo_statut.set("Fonctionnel")
combo_statut.pack(fill=tk.X, pady=(0, 10))

labels = ["Nom", "Type", "Quantité", "Fournisseur", "Remarque"]
entries = {}
for lab in labels:
    ttk.Label(left_panel, text=lab).pack(anchor="w", pady=(5, 0))
    entry = ttk.Entry(left_panel, width=30)
    entry.pack(fill=tk.X, pady=(0, 10))
    entries[lab] = entry

entry_nom = entries["Nom"]
entry_type = entries["Type"]
entry_quantite = entries["Quantité"]
entry_fournisseur = entries["Fournisseur"]
entry_remarque = entries["Remarque"]

# Boutons Gauche
btn_frame = ttk.Frame(left_panel)
btn_frame.pack(pady=20, fill=tk.X)
ttk.Button(btn_frame, text="AJOUTER / MÀJ", command=add_item).pack(fill=tk.X, pady=5)
ttk.Button(btn_frame, text="MODIFIER", command=update_item).pack(fill=tk.X, pady=5)
ttk.Button(btn_frame, text="SUPPRIMER", command=delete_item).pack(fill=tk.X, pady=5)
ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=15)
ttk.Button(left_panel, text="IMPORTER EXCEL", command=import_excel).pack(fill=tk.X, pady=5)
ttk.Button(left_panel, text="VIDER CHAMPS", command=clear_entries).pack(fill=tk.X, pady=5)

# Droite : Inventaire
right_panel = ttk.LabelFrame(main_container, text="Inventaire Global", padding="10")
right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

cols = ("ID", "Nom", "Type", "Quantité", "Fournisseur", "Remarque", "Statut")
tree = ttk.Treeview(right_panel, columns=cols, show='headings')
tree_scroll = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=tree_scroll.set)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

for col in cols:
    tree.heading(col, text=col)
    width = 100
    if col == "ID": width=40
    if col == "Quantité": width=60
    tree.column(col, width=width)

tree.pack(fill=tk.BOTH, expand=True)
tree.bind("<<TreeviewSelect>>", select_item)

# Tags de couleur
tree.tag_configure('low_stock', background=ALERT_LOW_STOCK) # Rouge pour stock faible
tree.tag_configure('panne', background=ALERT_BROKEN, foreground="#555555") # Gris pour panne

# Init
create_tables()
refresh_tree()

root.mainloop()
