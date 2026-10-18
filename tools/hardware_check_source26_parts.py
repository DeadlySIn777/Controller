"""Exact optional source26 identity checks, independent of synthesis or PCB state."""

CAPS = ('C14741', 'C14743')
FUSES = ('F11001', 'F11002', 'F11003')

def check_source26(parts, actual, model, mapping):
    errors = []
    metadata = model.get('adc_reference_component_qualification')
    ledger = mapping.get('reviewed_source26_qualification_delta')
    if metadata is None and ledger is None:
        return errors  # Frozen earlier revisions remain independently readable.
    if not ledger or ledger.get('references') != list(CAPS + FUSES):
        errors.append('Exact five-part source26 qualification ledger required')
    for ref, net in [('C14741', 'AI_ADC_REFIO'), ('C14743', 'AI_ADC_REFCAP')]:
        c = parts.get(ref, {})
        if (c.get('mpn') != 'GRM188R71E105KA12D' or c.get('value') != '1000nF25V'
                or c.get('voltage_rating_v') != 25
                or c.get('footprint') != 'Capacitor_SMD:C_0603_1608Metric'
                or abs(c.get('capacitance_f', 0) - 1e-6) > 1e-15):
            errors.append('Exact manufacturer-confirmed reference part required ' + ref)
        if (actual.get((ref, '1')) != '/motherboard_analog_input/' + net
                or actual.get((ref, '2')) != '/motherboard_analog_input/AI_AGND'):
            errors.append('Exact quiet reference source pins required ' + ref)
    for ref in FUSES:
        c = parts.get(ref, {})
        if c.get('mpn') != '3568' or c.get('footprint') != 'CNC_MB_Fuse:Keystone_3568_M55':
            errors.append('Exact manufacturer fuse mounting required ' + ref)
    if (not metadata or metadata.get('reference_effective_capacitance_full_corner_qualified') is not False
            or metadata.get('reference_ESR_loaded_stability_qualified') is not False
            or metadata.get('product_internal_ambient_c') != [0, 55]):
        errors.append('Source26 typical reference model cannot promise physical qualification or expanded temperature')
    return errors
