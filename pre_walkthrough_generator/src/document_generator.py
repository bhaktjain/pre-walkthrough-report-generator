from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image
import os

class DocumentGenerator:
    def __init__(self):
        self.doc = Document()
        self._setup_document()

    def _setup_document(self):
        """Set up document styles and formatting"""
        # Add styles for different heading levels
        for i in range(1, 4):
            style = self.doc.styles.add_style(f'CustomHeading{i}', WD_STYLE_TYPE.PARAGRAPH)
            font = style.font
            font.size = Pt(16 - (i * 2))
            font.bold = True
            font.color.rgb = RGBColor(0, 0, 0)
        
        # Add header and footer
        self._add_header_footer()

    def _format_value(self, value, prefix="", suffix=""):
        """Format a value with optional prefix and suffix"""
        if value is None:
            return "Information not available"
        if isinstance(value, (int, float)) and prefix == "$":
            return f"{prefix}{value:,}{suffix}"
        return f"{prefix}{value}{suffix}"

    def _format_currency(self, value: Optional[int], prefix: str = "$") -> str:
        """Format a currency value with proper formatting"""
        if value is None:
            return "TBD"
        return f"{prefix}{value:,}"

    def _add_header_footer(self):
        """Add header and footer images to the document"""
        try:
            # Get the header and footer image paths
            header_path = "header.png"
            footer_path = "footer.png"
            
            # Check if files exist
            if not os.path.exists(header_path) or not os.path.exists(footer_path):
                print(f"Warning: Header or footer image not found. Header: {os.path.exists(header_path)}, Footer: {os.path.exists(footer_path)}")
                return
            
            # Access the document's sections
            section = self.doc.sections[0]
            
            # Add header
            header = section.header
            header_para = header.paragraphs[0]
            header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add header image - much smaller size
            run = header_para.runs[0] if header_para.runs else header_para.add_run()
            run.add_picture(header_path, height=Inches(0.8))  # Small header
            
            # Add spacing after header
            header_para.paragraph_format.space_after = Pt(12)
            
            # Add footer
            footer = section.footer
            footer_para = footer.paragraphs[0]
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add footer image - much smaller size
            run = footer_para.runs[0] if footer_para.runs else footer_para.add_run()
            run.add_picture(footer_path, height=Inches(0.8))  # Small footer
            
            print("Header and footer images added successfully")
            
        except Exception as e:
            print(f"Error adding header/footer: {e}")

    def _add_header(self, data: Dict[str, Any]):
        """Add document header with title and address"""
        # Add title
        title = self.doc.add_heading('Pre-Walkthrough Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add address
        address = data.get('property_address', '')
        if address:
            addr_para = self.doc.add_paragraph()
            addr_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            addr_para.add_run(address).bold = True
        
        # Add date
        date_para = self.doc.add_paragraph()
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        date_para.add_run(datetime.now().strftime("%B %d, %Y"))
        
        self.doc.add_paragraph()

    def _add_executive_summary(self, data: Dict[str, Any]):
        """Add concise, sales-focused executive summary"""
        self.doc.add_heading('Executive Summary', level=1)

        transcript = data.get('transcript_info', {})
        scope = transcript.get('renovation_scope', {})

        # Build key sentences
        # 1. Project Goals (comprehensive project description)
        goals_parts = []
        
        # Add kitchen goals
        kitchen = scope.get('kitchen', {})
        if kitchen.get('description'):
            goals_parts.append(f"Kitchen: {kitchen['description']}")
        
        # Add bathroom goals
        bathrooms = scope.get('bathrooms', {})
        if bathrooms.get('plumbing_changes') or bathrooms.get('specific_requirements'):
            bath_desc = []
            if bathrooms.get('plumbing_changes'):
                bath_desc.append(bathrooms['plumbing_changes'])
            if bathrooms.get('specific_requirements'):
                bath_desc.extend(bathrooms['specific_requirements'])
            goals_parts.append(f"Bathroom: {', '.join(bath_desc)}")
        
        # Add additional work goals
        additional = scope.get('additional_work', {})
        if additional.get('rooms') or additional.get('structural_changes') or additional.get('systems_updates'):
            add_desc = []
            if additional.get('rooms'):
                add_desc.append(f"Rooms: {', '.join(additional['rooms'])}")
            if additional.get('structural_changes'):
                add_desc.append(f"Structural: {', '.join(additional['structural_changes'])}")
            if additional.get('systems_updates'):
                add_desc.append(f"Systems: {', '.join(additional['systems_updates'])}")
            goals_parts.append(f"Additional work: {', '.join(add_desc)}")
        
        project_goals = '. '.join(goals_parts) or 'Comprehensive renovation project'

        # 2. Client Drivers – derive simple reasons
        drivers = []
        add_work = scope.get('additional_work', {})
        if add_work.get('structural_changes'):
            drivers.append('layout upgrade')
        if add_work.get('systems_updates'):
            drivers.append('systems modernisation')
        client_drivers = ', '.join(drivers) or 'home improvement'

        # 3. Key numbers – budget + timeline
        min_total, max_total = 0, 0 # Initialize to 0
        timeline = scope.get('timeline', {})
        duration = timeline.get('total_duration', 'TBD')

        # Build budget phrase smartly - check for per sq ft cost first
        additional_work = scope.get('additional_work') or {}
        estimated_costs = additional_work.get('estimated_costs') or {}
        per_sqft_cost = estimated_costs.get('per_sqft_cost')
        total_range = estimated_costs.get('total_estimated_range') or {}
        
        # If we have per sq ft cost, use that as the primary budget info
        if per_sqft_cost:
            if total_range.get('min') and total_range.get('max'):
                budget_phrase = f"Budget ${per_sqft_cost}/sq ft (estimated ${total_range['min']:,} – ${total_range['max']:,})"
            elif total_range.get('min'):
                budget_phrase = f"Budget ${per_sqft_cost}/sq ft (estimated from ${total_range['min']:,})"
            else:
                budget_phrase = f"Budget from ${per_sqft_cost}/sq ft"
        else:
            # Fallback to old logic for projects without per sq ft pricing
            kitchen = scope.get('kitchen') or {}
            kitchen_cost = kitchen.get('estimated_cost') or {}
            kitchen_range = kitchen_cost.get('range') or {}
            if kitchen_range.get('min'):
                kmin = scope['kitchen']['estimated_cost']['range']['min']
                kmax = scope['kitchen']['estimated_cost']['range']['max']
                min_total += kmin
                max_total += kmax if kmax else kmin # Use max if available, otherwise min
            bathrooms = scope.get('bathrooms') or {}
            if bathrooms.get('count') and bathrooms.get('cost_per_bathroom'):
                cost = bathrooms['cost_per_bathroom']
                count = int(bathrooms['count'])  # Convert to int for range()
                for i in range(1, count + 1):
                    min_total += cost
                    max_total += cost # Assuming max is the same as min for simplicity here
            
            for item, cost in estimated_costs.items():
                if isinstance(cost, (int, float)) and item != 'per_sqft_cost':
                    min_total += cost
                    max_total += cost # Assuming max is the same as min for simplicity here

            if min_total and max_total and max_total != min_total:
                budget_phrase = f"Budget ${min_total:,} – ${max_total:,}"
            elif min_total and (not max_total or max_total == min_total):
                budget_phrase = f"Budget from ${min_total:,} (upper bound TBD)"
            else:
                budget_phrase = None  # unknown

        key_parts = []
        if budget_phrase:
            key_parts.append(budget_phrase)
        if duration and duration.lower() not in {"tbd", "unknown"}:
            key_parts.append(f"Target window {duration}")
        key_numbers = '; '.join(key_parts) if key_parts else 'Key numbers TBD'

        # Add numbered bullets
        bullets = [f"1. Project Goals – {project_goals}.",
                   f"2. Client Drivers – {client_drivers}.",
                   f"3. Key Numbers – {key_numbers}."]
        for text in bullets:
            para = self.doc.add_paragraph(text, style='List Bullet')
            para.paragraph_format.space_after = Pt(6)

    def _add_property_details(self, data: Dict[str, Any]):
        """Add property details section"""
        self.doc.add_heading('Property Details', level=1)
        
        # Create property details table without empty header row
        table = self.doc.add_table(rows=0, cols=2)
        table.style = 'Table Grid'
        table.autofit = True

        # Add property details
        property_info = data.get('property_details', {}) or {}
        
        # Format price if available, fallback to last sold price
        price = property_info.get('price', 'Information not available')
        last_sold_price = property_info.get('last_sold_price')
        last_sold_date = property_info.get('last_sold_date')
        
        if isinstance(price, (int, float)):
            price_display = f"${price:,.2f}"
        elif price not in (None, '', 'Information not available'):
            # Try to parse as float if possible
            try:
                price_num = float(price.replace(',', '').replace('$', ''))
                price_display = f"${price_num:,.2f}"
            except Exception:
                price_display = str(price)
        elif last_sold_price and last_sold_date:
            # Use last sold price if current price not available
            if isinstance(last_sold_price, (int, float)):
                price_display = f"Last sold: ${last_sold_price:,.2f} ({last_sold_date})"
            else:
                try:
                    price_num = float(str(last_sold_price).replace(',', '').replace('$', ''))
                    price_display = f"Last sold: ${price_num:,.2f} ({last_sold_date})"
                except Exception:
                    price_display = f"Last sold: {last_sold_price} ({last_sold_date})"
        else:
            price_display = 'Contact broker for pricing'

        # Format HOA fee if available
        hoa_fee_raw = property_info.get('hoa_fee', 'Information not available')
        if isinstance(hoa_fee_raw, (int, float)):
            hoa_fee_display = f"${hoa_fee_raw:,.2f}/month"
        elif hoa_fee_raw not in (None, '', 'Information not available'):
            try:
                hoa_fee_num = float(hoa_fee_raw.replace(',', '').replace('$', ''))
                hoa_fee_display = f"${hoa_fee_num:,.2f}/month"
            except Exception:
                hoa_fee_display = str(hoa_fee_raw)
        else:
            hoa_fee_display = 'Information not available'

        # For each property detail, handle as string/number, not dict
        def safe_get(info, key):
            return info[key] if key in info and info[key] not in (None, '', []) else 'Information not available'

        # Get all property details using safe_get
        bedrooms = safe_get(property_info, 'bedrooms')
        bathrooms = safe_get(property_info, 'bathrooms')
        sqft = safe_get(property_info, 'sqft')
        year_built = safe_get(property_info, 'year_built')
        property_type = safe_get(property_info, 'property_type')
        neighborhood = safe_get(property_info, 'neighborhood')
        rooms = safe_get(property_info, 'rooms')
        last_sold_price = safe_get(property_info, 'last_sold_price')
        last_sold_date = safe_get(property_info, 'last_sold_date')
        
        # Create the details table
        details = [
            ('Current Price', price_display),
            ('Square Footage', f"{sqft} sq ft"),
            ('Bedrooms', bedrooms),
            ('Bathrooms', bathrooms),
            ('Year Built', year_built),
            ('Property Type', property_type),
            ('HOA Fee', hoa_fee_display),
            ('Neighborhood', neighborhood)
        ]

        for item, detail in details:
            row_cells = table.add_row().cells
            row_cells[0].text = item
            row_cells[1].text = str(detail)

    def _download_image(self, url: str) -> Optional[BytesIO]:
        """Download image from URL and return as BytesIO object. If not supported, try converting to PNG."""
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Try to open with PIL to ensure it's a supported format
                try:
                    from PIL import Image
                    img = Image.open(BytesIO(response.content))
                    # Convert to PNG in memory if not already
                    if img.format != 'PNG':
                        output = BytesIO()
                        img.save(output, format='PNG')
                        output.seek(0)
                        return output
                    else:
                        return BytesIO(response.content)
                except Exception as pil_e:
                    print(f"[ERROR] PIL could not process image: {pil_e}")
                    # Fallback: return raw bytes
                    return BytesIO(response.content)
            else:
                print(f"[ERROR] Image download failed: {url} (status {response.status_code})")
        except Exception as e:
            print(f"[ERROR] Exception downloading image: {url} - {e}")
        return None

    def _add_client_details(self, data: Dict[str, Any]):
        """Add client details section"""
        self.doc.add_heading('Client Details', level=1)
        
        # Get client info from transcript data
        transcript_info = data.get('transcript_info', {})
        client_info = transcript_info.get('client_info', {})
        
        # Create client details table without empty first row
        table = self.doc.add_table(rows=0, cols=2)
        table.style = 'Table Grid'
        table.autofit = True
        
        # Format names
        names = client_info.get('names', [])
        names_str = ', '.join(names) if names else 'N/A'
        
        # Format preferences
        preferences = client_info.get('preferences', {})
        pref_items = []
        for key, value in preferences.items():
            if value:
                formatted_key = key.replace('_', ' ').title()
                pref_items.append(f"{formatted_key}: {value}")
        preferences_str = '\n'.join(pref_items) if pref_items else 'N/A'
        
        # Format constraints
        constraints = client_info.get('constraints', [])
        constraints_str = '\n'.join(constraints) if constraints else 'N/A'
        
        # Format red flags
        red_flags = client_info.get('red_flags', {})
        flag_items = []
        for key, value in red_flags.items():
            if value:
                formatted_key = key.replace('_', ' ').title()
                flag_items.append(formatted_key)
        red_flags_str = '\n'.join(flag_items) if flag_items else 'None'
        
        details = [
            ('Name', names_str),
            ('Phone', client_info.get('phone') or 'N/A'),
            ('Profession', client_info.get('profession') or 'N/A'),
            ('Preferences', preferences_str),
            ('Constraints', constraints_str),
            ('Potential Concerns', red_flags_str)
        ]
        
        for item, detail in details:
            row_cells = table.add_row().cells
            row_cells[0].text = item
            row_cells[1].text = str(detail)

    def _add_hyperlink(self, paragraph, text: str, url: str) -> None:
        """Add a hyperlink to a paragraph"""
        # This gets access to the document.xml.rels file and gets a new relation id value
        part = paragraph._parent.part
        r_id = part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

        # Create the w:hyperlink tag and add needed values
        hyperlink = OxmlElement('w:hyperlink')
        hyperlink.set(qn('r:id'), r_id)

        # Create a new run object (a wrapper for text)
        new_run = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')

        # Add color and underline to hyperlink
        c = OxmlElement('w:color')
        c.set(qn('w:val'), '0000FF')
        rPr.append(c)

        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)

        new_run.append(rPr)
        new_run.text = text
        hyperlink.append(new_run)

        # Add the hyperlink to the paragraph
        paragraph._p.append(hyperlink)

    def _add_property_links(self, data: Dict[str, Any]):
        """Add property links section"""
        self.doc.add_heading('Property Links', level=1)
        
        property_details = data.get('property_details') or {}

        realtor_url = data.get('realtor_url')
        if not realtor_url:
            # Fallback construct if not provided
            pid = data.get('property_id')
            address = data.get('property_address', '')
            if pid and address:
                parts = [p.strip() for p in address.split(',') if p.strip()]
                if len(parts) >= 3:
                    street = parts[0].replace(' ', '-')
                    city = parts[-2].replace(' ', '-')
                    state_zip = parts[-1].split()
                    if len(state_zip) >= 2:
                        state = state_zip[0]
                        zip_code = state_zip[1]
                        realtor_url = f"https://www.realtor.com/realestateandhomes-detail/{street}_{city}_{state}_{zip_code}_M{pid}"

        link_para = self.doc.add_paragraph()
        link_para.add_run('• Realtor.com: ').bold = True
        if realtor_url:
            self._add_hyperlink(link_para, 'View Listing', realtor_url)
        else:
            link_para.add_run('N/A')
        
        # Add Floor Plan section
        self.doc.add_heading('Floor Plan', level=2)
        floor_plans_data = data.get('floor_plans') or {}
        floor_plans = floor_plans_data.get('floor_plans', []) or property_details.get('floor_plans', [])
        
        if floor_plans:
            for plan in floor_plans:
                if plan.get('url'):
                    # Try to download and embed the image
                    image_stream = self._download_image(plan['url'])
                    if image_stream:
                        try:
                            self.doc.add_picture(image_stream, width=Inches(6.0))
                            link_para = self.doc.add_paragraph()
                            link_para.add_run('Floor plan link: ').bold = True
                            self._add_hyperlink(link_para, plan['url'], plan['url'])
                            self.doc.add_paragraph()
                        except Exception as e:
                            print(f"[ERROR] Exception embedding image: {plan['url']} - {e}")
                            # Fallback: try to convert to PNG and embed
                            try:
                                from PIL import Image
                                response = requests.get(plan['url'])
                                img = Image.open(BytesIO(response.content))
                                output = BytesIO()
                                img.save(output, format='PNG')
                                output.seek(0)
                                self.doc.add_picture(output, width=Inches(6.0))
                                link_para = self.doc.add_paragraph()
                                link_para.add_run('Floor plan link: ').bold = True
                                self._add_hyperlink(link_para, plan['url'], plan['url'])
                                self.doc.add_paragraph()
                            except Exception as e2:
                                print(f"[ERROR] Fallback PNG conversion failed: {plan['url']} - {e2}")
                                link_para = self.doc.add_paragraph()
                                link_para.add_run('Floor plan link: ').bold = True
                                self._add_hyperlink(link_para, plan['url'], plan['url'])
                    else:
                        print(f"[ERROR] Could not download floor plan image: {plan['url']}")
                        link_para = self.doc.add_paragraph()
                        link_para.add_run('Floor plan link: ').bold = True
                        self._add_hyperlink(link_para, plan['url'], plan['url'])
        else:
            self.doc.add_paragraph('No floor plans available.')

    def _add_section_break(self):
        """Add a section break for clarity"""
        self.doc.add_paragraph()

    def _add_building_requirements(self, data: Dict[str, Any]):
        """Add building requirements section from transcript data only (no hard-coded rules)."""
        self.doc.add_heading('Building Requirements', level=1)

        transcript_info = data.get('transcript_info', {})
        property_info = transcript_info.get('property_info', {}) or {}

        # Collect any explicit rules that were captured
        rules_list = property_info.get('building_rules', []) if isinstance(property_info.get('building_rules'), list) else []

        # If we have nothing, state N/A and return
        if not rules_list:
            self.doc.add_paragraph('N/A')
            return

        # Otherwise, list each rule as a bullet point
        for rule in rules_list:
            self.doc.add_paragraph(f"• {rule}")

    def _add_renovation_scope(self, data: Dict[str, Any]):
        """Add renovation scope section"""
        self.doc.add_heading('Renovation Scope', level=1)
        
        # Get renovation info from transcript data
        transcript_info = data.get('transcript_info') or {}
        renovation = transcript_info.get('renovation_scope') or {}
        
        # Loop dynamically through each scope section; skip 'timeline' (rendered separately)
        for section_name, section in renovation.items():
            if section_name.lower() == 'timeline':
                continue  # handled in dedicated timeline section
            if not isinstance(section, dict) or all(v in (None, '', [], {}) for v in section.values()):
                continue
            self.doc.add_heading(section_name.replace('_', ' ').title(), level=2)
            table = self.doc.add_table(rows=0, cols=2)
            table.style = 'Table Grid'
            for key, value in section.items():
                if value in (None, '', [], {}):
                    continue
                pretty_value = self._stringify(value)
                row = table.add_row().cells
                row[0].text = key.replace('_', ' ').title()
                row[1].text = pretty_value

    def _add_timeline_phasing(self, data: Dict[str, Any]):
        """Add timeline and phasing section dynamically (no default placeholder values)."""
        self.doc.add_heading('Timeline & Phasing', level=1)

        transcript_info = data.get('transcript_info') or {}
        renovation_scope = transcript_info.get('renovation_scope') or {}
        timeline = renovation_scope.get('timeline') or {}

        # Map readable labels to transcript keys
        key_map = {
            'total_duration': 'Total Duration',
            'phasing': 'Phasing',
            'living_arrangements': 'Occupancy',
            'coordination': 'Coordination'
        }

        if not any(v for v in timeline.values() if v not in (None, '', [], {})):
            self.doc.add_paragraph('N/A')
            return

        table = self.doc.add_table(rows=0, cols=2)
        table.style = 'Table Grid'

        for key, label in key_map.items():
            val = timeline.get(key)
            if val not in (None, '', [], {}):
                row = table.add_row().cells
                row[0].text = label
                row[1].text = str(val)

    def _add_budget_summary(self, data: Dict[str, Any]):
        """Add budget summary section"""
        self.doc.add_heading('Budget Summary', level=1)
        
        table = self.doc.add_table(rows=0, cols=2)
        table.style = 'Table Grid'
        
        transcript_info = data.get('transcript_info') or {}
        renovation = transcript_info.get('renovation_scope') or {}
        kitchen = renovation.get('kitchen', {})
        bathrooms = renovation.get('bathrooms', {})
        additional = renovation.get('additional_work', {})
        
        details = []
        # Kitchen cost
        kitchen_cost = kitchen.get('estimated_cost') or {}
        kitchen_range = kitchen_cost.get('range') or {}
        if kitchen_range.get('min'):
            kmin = kitchen['estimated_cost']['range']['min']
            kmax = kitchen['estimated_cost']['range']['max']
            details.append(('Kitchen Total', f"{self._format_currency(kmin)} - {self._format_currency(kmax) if kmax else 'TBD'}"))

        # Bathrooms cost
        if bathrooms.get('count') and bathrooms.get('cost_per_bathroom'):
            cost = self._format_currency(bathrooms['cost_per_bathroom'])
            count = int(bathrooms['count'])  # Convert to int for range()
            for i in range(1, count + 1):
                details.append((f"Bathroom {i}", f"~{cost}"))

        # Additional work estimated_costs dict supports arbitrary entries
        for item, cost in additional.get('estimated_costs', {}).items():
            if isinstance(cost, (int, float)):
                details.append((item.replace('_',' ').title(), self._format_currency(cost)))
        
        # Total
        min_total, max_total = 0, 0 # Initialize to 0
        kitchen_cost = kitchen.get('estimated_cost') or {}
        kitchen_range = kitchen_cost.get('range') or {}
        if kitchen_range.get('min'):
            kmin = kitchen['estimated_cost']['range']['min']
            kmax = kitchen['estimated_cost']['range']['max']
            min_total += kmin
            max_total += kmax if kmax else kmin
        if bathrooms.get('count') and bathrooms.get('cost_per_bathroom'):
            cost = bathrooms['cost_per_bathroom']
            count = int(bathrooms['count'])  # Convert to int for range()
            for i in range(1, count + 1):
                min_total += cost
                max_total += cost
        for item, cost in additional.get('estimated_costs', {}).items():
            if isinstance(cost, (int, float)):
                min_total += cost
                max_total += cost

        if min_total and max_total and max_total != min_total:
            details.append(('Total Range', f"{self._format_currency(min_total)} - {self._format_currency(max_total)}"))
        elif min_total and (not max_total or min_total == max_total):
            details.append(('Total Minimum', f"{self._format_currency(min_total)}"))
        
        # Create table rows
        for item, detail in details:
            row_cells = table.add_row().cells
            row_cells[0].text = item
            row_cells[1].text = str(detail)

    def _add_notes(self, data: Dict[str, Any]):
        """Add notes section"""
        self.doc.add_heading('Notes:', level=1)
        
        transcript_info = data.get('transcript_info', {})
        renovation = transcript_info.get('renovation_scope', {})
        materials = transcript_info.get('materials_and_design', {})
        project_mgmt = transcript_info.get('project_management', {})
        
        notes = []
        
        # Material sourcing
        if materials.get('sourcing_responsibility'):
            notes.append(f"• {materials['sourcing_responsibility']}")
        
        # Specific requirements
        kitchen_reno = renovation.get('kitchen') or {}
        if kitchen_reno.get('specific_requirements'):
            notes.extend(f"• {req}" for req in kitchen_reno['specific_requirements'])
        bathrooms_reno = renovation.get('bathrooms') or {}
        if bathrooms_reno.get('specific_requirements'):
            notes.extend(f"• {req}" for req in bathrooms_reno['specific_requirements'])
        
        # Project management notes
        if project_mgmt.get('communication_preferences'):
            notes.append(f"• Communication preference: {project_mgmt['communication_preferences']}")
        if project_mgmt.get('documentation_needs'):
            notes.extend(f"• {doc}" for doc in project_mgmt['documentation_needs'])
        
        # Add default notes if none found
        if not notes:
            notes = ['• No special notes recorded.']
        
        notes = [n for n in notes if n.lower() not in {'unknown','n/a','none'}]
        if not notes:
            notes = ['• No special notes recorded.']
        
        for note in notes:
            self.doc.add_paragraph(note)
    
    def _add_neighboring_projects(self, data: Dict[str, Any]):
        """Add neighboring projects section from Zoho CRM"""
        self.doc.add_heading('Neighboring Projects', level=1)
        
        neighboring_projects = data.get('neighboring_projects', [])
        
        if not neighboring_projects:
            self.doc.add_paragraph("No neighboring projects found in this area.")
            return
        
        # Add intro text
        same_building = [p for p in neighboring_projects if p.get('is_same_building')]
        if same_building:
            intro = f"Found {len(same_building)} project(s) in the same building"
            if len(neighboring_projects) > len(same_building):
                intro += f" and {len(neighboring_projects) - len(same_building)} in the neighborhood."
            else:
                intro += "."
        else:
            intro = f"Found {len(neighboring_projects)} project(s) in the neighborhood."
        
        self.doc.add_paragraph(intro)
        self.doc.add_paragraph()  # Spacing
        
        # Create table with same style as other tables
        table = self.doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'  # Match other tables in the document
        table.autofit = True
        
        # Header row
        header_cells = table.rows[0].cells
        headers = ['Project Address', 'Amount', 'Stage', 'Location']
        for i, header in enumerate(headers):
            header_cells[i].text = header
            # Make header bold
            for paragraph in header_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
        
        # Add project rows
        for project in neighboring_projects:
            row_cells = table.add_row().cells
            
            # Project address/name
            row_cells[0].text = project.get('deal_name', 'N/A')
            
            # Amount
            amount = project.get('amount')
            if amount and amount > 0:
                row_cells[1].text = f"${amount:,}"
            else:
                row_cells[1].text = "TBD"
            
            # Stage/Status
            stage = project.get('stage', 'Unknown')
            row_cells[2].text = stage
            
            # Location indicator
            if project.get('is_same_building'):
                row_cells[3].text = "Same Building"
            else:
                row_cells[3].text = "Neighborhood"

    def generate_report(self, data: Dict[str, Any], output_dir: str = "data", file_name: str = None) -> Optional[str]:
        """Generate the pre-walkthrough report"""
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Add sections in order
            self._add_header(data)  # Title, address, date
            self._add_section_break()
            
            self._add_executive_summary(data)  # Project overview, scope, timeline, budget
            self._add_section_break()
            
            self._add_property_details(data)  # Property information from API
            self._add_section_break()
            
            self._add_client_details(data)  # Client information from transcript
            self._add_section_break()
            
            self._add_property_links(data)  # Realtor.com link and floor plans
            self._add_section_break()
            
            self._add_building_requirements(data)  # Co-op requirements from transcript
            self._add_section_break()
            
            self._add_renovation_scope(data)  # Kitchen and bathroom details
            self._add_section_break()
            
            self._add_timeline_phasing(data)  # Timeline and living arrangements
            self._add_section_break()
            
            self._add_budget_summary(data)  # Cost breakdown
            self._add_section_break()
            
            self._add_neighboring_projects(data)  # Neighboring projects from Zoho CRM
            self._add_section_break()
            
            self._add_notes(data)  # Additional notes and requirements
            
            # Save the document
            if not file_name:
                # build from address - sanitize for filename
                addr = data.get('property_address','report').split(',')[0]
                # Remove invalid filename characters
                invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '#']
                for char in invalid_chars:
                    addr = addr.replace(char, '_')
                addr = addr.replace(' ', '_')
                # Replace multiple underscores with single
                while '__' in addr:
                    addr = addr.replace('__', '_')
                addr = addr.strip('_')
                file_name = f"PreWalk_{addr}.docx"
            output_path = output_dir / file_name
            self.doc.save(str(output_path))
            print(f"\nReport generated successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"\nError generating report: {e}")
            import traceback
            traceback.print_exc()
            return None 

    # ------------------------------------------------------------------
    # Helper to stringify complex values for tables
    # ------------------------------------------------------------------

    def _stringify(self, value):
        """Convert list/dict to human-readable string without brackets/quotes."""
        if isinstance(value, list):
            return ', '.join(str(v) for v in value)
        if isinstance(value, dict):
            parts = []
            for k, v in value.items():
                if isinstance(v, dict):
                    sub = ', '.join(f"{sk}: {sv}" for sk, sv in v.items() if sv not in (None, '', [], {}))
                    parts.append(f"{k.title()} → {sub}")
                else:
                    parts.append(f"{k.replace('_',' ').title()}: {v}")
            return '; '.join(parts)
        return str(value) 