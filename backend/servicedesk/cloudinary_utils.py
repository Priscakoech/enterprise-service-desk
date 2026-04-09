"""
Cloudinary upload helpers.

All user-uploaded media (ticket attachments, profile pictures) is stored in
Cloudinary.  Only the returned ``secure_url`` is persisted in the database.
"""

import logging
import cloudinary.uploader

logger = logging.getLogger(__name__)

# Extensions recognised as raster/vector images by Cloudinary's "image" pipeline.
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico'}

# Everything else we accept is uploaded as a raw file.
DOCUMENT_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv', 'ppt', 'pptx',
    'odt', 'ods', 'odp', 'rtf', 'zip', 'rar', '7z',
}

ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS

MAX_FILE_SIZE_MB = 25  # Cloudinary free-tier limit


def _extension(filename: str) -> str:
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def validate_file(uploaded_file) -> tuple[str, str]:
    """Validate an uploaded file and return ``(extension, file_type)``.

    Raises ``ValueError`` with a user-friendly message on failure.
    """
    filename = getattr(uploaded_file, 'name', '')
    ext = _extension(filename)

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f'File type .{ext} is not allowed. '
            f'Accepted: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
        )

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f'File is too large ({size_mb:.1f} MB). Maximum allowed is {MAX_FILE_SIZE_MB} MB.'
        )

    file_type = 'image' if ext in IMAGE_EXTENSIONS else 'document'
    return ext, file_type


def upload_to_cloudinary(uploaded_file, *, folder: str = 'servicedesk') -> str:
    """Upload a Django ``UploadedFile`` to Cloudinary and return the secure URL.

    * Images are uploaded with ``resource_type='image'``
    * Documents (PDF, DOCX, …) are uploaded with ``resource_type='raw'``

    Returns the ``secure_url`` string from Cloudinary's response.
    Raises ``RuntimeError`` on upload failure.
    """
    filename = getattr(uploaded_file, 'name', 'file')
    ext = _extension(filename)
    resource_type = 'image' if ext in IMAGE_EXTENSIONS else 'raw'

    try:
        result = cloudinary.uploader.upload(
            uploaded_file,
            resource_type=resource_type,
            folder=folder,
            use_filename=True,
            unique_filename=True,
        )
        url = result.get('secure_url')
        if not url:
            raise RuntimeError('Cloudinary returned no secure_url')
        logger.info('Uploaded %s to Cloudinary (%s): %s', filename, resource_type, url)
        return url
    except Exception as exc:
        logger.error('Cloudinary upload failed for %s: %s', filename, exc)
        raise RuntimeError(f'File upload failed: {exc}') from exc


def upload_profile_picture(uploaded_file) -> str:
    """Convenience wrapper for profile picture uploads.

    Images are uploaded to the ``servicedesk/profiles`` folder and
    auto-cropped to a square thumbnail by Cloudinary.
    """
    try:
        result = cloudinary.uploader.upload(
            uploaded_file,
            resource_type='image',
            folder='servicedesk/profiles',
            use_filename=True,
            unique_filename=True,
            transformation=[
                {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
            ],
        )
        url = result.get('secure_url')
        if not url:
            raise RuntimeError('Cloudinary returned no secure_url')
        logger.info('Uploaded profile picture to Cloudinary: %s', url)
        return url
    except Exception as exc:
        logger.error('Profile picture upload failed: %s', exc)
        raise RuntimeError(f'Profile picture upload failed: {exc}') from exc
