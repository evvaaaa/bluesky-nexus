"""Pydantic schema for defining connections between `HasHints` devices and
nexusformat base classes for the XraySpectroscopy nexus definitions fork:

https://github.com/XraySpectroscopy/nexus_definitions

This is in use at esrf:

https://nxxas-hdf5-nexus-7ba1891a1aaa2d29580131298dc337bab2b3e5de32b6ef.gitlab-pages.esrf.fr/classes/applications/NXxas_new.html

The only additions here over `nexusformat_schema` is the `NXxas_new` application definition, which
is more suited to xas.
"""
