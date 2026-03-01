# -*- coding: utf-8 -*-
import base64
import hashlib
from io import BytesIO
from dataclasses import dataclass

from odoo import _
from odoo.exceptions import UserError

from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader

@dataclass
class PreparedPades:
    placeholder_pdf: bytes
    bytes_to_sign: bytes

class PadesCms:
    """
    Prepare placeholder + get bytes-to-sign (TBS)
    Then embed CMS/PKCS#7 SignedData returned by SmartCA into placeholder PDF.
    """

    def prepare_placeholder_and_tbs(self, original_pdf_bytes: bytes, field_name: str, reason: str, location: str) -> PreparedPades:
        try:
            reader = PdfFileReader(original_pdf_bytes)
            w = IncrementalPdfFileWriter.from_reader(reader)

            meta = signers.PdfSignatureMetadata(
                field_name=field_name,
                reason=reason,
                location=location,
            )

            dummy = signers.ExternalSigner(signing_cert=None, cert_registry=None, signature_mechanism=None)

            pdf_signer = signers.PdfSigner(
                signature_meta=meta,
                signer=dummy,
                existing_fields_only=False,
                new_field_spec=SigFieldSpec(sig_field_name=field_name),
            )

            session = pdf_signer.init_signing_session(w)
            tbs = session.get_bytes_to_sign()

            out = BytesIO()
            w.write(out)
            placeholder_pdf = out.getvalue()

            return PreparedPades(placeholder_pdf=placeholder_pdf, bytes_to_sign=tbs)
        except Exception as e:
            raise UserError(_("PAdES prepare failed: %s") % e)

    def tbs_sha256_hex_upper(self, bytes_to_sign: bytes) -> str:
        return hashlib.sha256(bytes_to_sign).hexdigest().upper()

    def embed_cms_into_placeholder_pdf(self, placeholder_pdf_bytes: bytes, cms_signature_b64: str, field_name: str) -> bytes:
        try:
            cms = base64.b64decode(cms_signature_b64)
        except Exception as e:
            raise UserError(_("Invalid CMS base64: %s") % e)

        try:
            reader = PdfFileReader(placeholder_pdf_bytes)
            w = IncrementalPdfFileWriter.from_reader(reader)

            meta = signers.PdfSignatureMetadata(field_name=field_name)

            class _PrecomputedCMSSigner(signers.ExternalSigner):
                def __init__(self, cms_bytes: bytes):
                    super().__init__(signing_cert=None, cert_registry=None, signature_mechanism=None)
                    self._cms = cms_bytes

                async def async_sign_raw(self, data: bytes, digest_algorithm: str, dry_run: bool = False) -> bytes:
                    return (b"\x00" * len(self._cms)) if dry_run else self._cms

            signer = _PrecomputedCMSSigner(cms)
            pdf_signer = signers.PdfSigner(signature_meta=meta, signer=signer, existing_fields_only=False)
            out = pdf_signer.sign_pdf(w)
            return out.getvalue()
        except Exception as e:
            raise UserError(_("PAdES embed failed: %s") % e)