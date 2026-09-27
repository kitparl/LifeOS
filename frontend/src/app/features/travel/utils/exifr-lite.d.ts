/** exifr's "lite" build (JPEG/HEIC/TIFF + GPS) has the same API as the package root, minus rarely used parsers. */
declare module 'exifr/dist/lite.esm.mjs' {
  import exifr from 'exifr';
  export default exifr;
}
