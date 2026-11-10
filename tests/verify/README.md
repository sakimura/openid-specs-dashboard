# Manual verification records

Checks that the Node and Python tests cannot cover: the built page in a real browser,
and exported CSV files in real spreadsheet applications.

All results below are from 2026-11-10, against commit `2bc92ff` and the `github-pages`
artifact of [workflow run 42608983611](https://github.com/sakimura/openid-specs-dashboard/actions/runs/42608983611).
The artifact's `app.js` is byte-identical to `public/app.js` at that commit. The CSV
check then used the same artifact with one change: the `app.js` from this branch, which
adds a UTF-8 BOM to the export.

## Repeating the checks

Download and unpack the artifact, then build one site per scenario:

```bash
gh run download 42608983611 --repo sakimura/openid-specs-dashboard --name github-pages --dir artifact
mkdir artifact/site && tar -xf artifact/artifact.tar -C artifact/site
python3 tests/verify/build_fixtures.py artifact/site fixtures
python3 -m http.server 8766 --directory fixtures
```

Each scenario is served at `http://localhost:8766/<scenario>/`. Only `data/specs.json`
differs from the artifact. Artifacts built before the BOM change need this branch's
`public/app.js` copied over `artifact/site/app.js` first.

## Malformed metadata in the browser (issue #8)

Browser: Chromium 152.0.7977.167 (Claude desktop app browser pane), macOS 26.3.

The public page, with its normal data, showed 101 rows and 13 working groups in the
chart, with no console errors.

| Scenario (`build_fixtures.py`) | Change to the data | Rows | WG chart rows | `Object.prototype` own properties | Console errors |
|---|---|---|---|---|---|
| `baseline` | none | 101 | 13 | 12 (standard) | none |
| `workgroup-proto` | `workgroup: "__proto__"` on `authorization-api-1_0` | 101 | 13, one labelled `__proto__` | 12 (standard) | none |
| `workgroup-constructor` | `workgroup: "constructor"`, same record | 101 | 13, one labelled `constructor` | 12 (standard) | none |
| `workgroup-tostring` | `workgroup: "toString"`, same record | 101 | 13, one labelled `toString` | 12 (standard) | none |
| `status-constructor` | `status: "constructor"` on `fapi-attacker-model-2_0` | 100, record dropped | 13 | 12 (standard) | none |
| `no-revision` | no revisions, URL, latest or milestone on `fapi-message-signing-2_0` | 100, record dropped | 13 | 12 (standard) | none |

A hostile working group name is a valid record, so it stays in the list and appears as
plain text in the chart. An uncaught error thrown on purpose did appear in the console
reader, so "none" is a real result.

## CSV formulas in spreadsheets (issue #9)

- `csv-formula-fixture.csv` is the page's own export from the `csv` scenario. It has
  21 formula-shaped and control titles, plus `=1+1` as an editor and `@SUM(1,1)` as a
  working group. The cases are listed in `CSV_TITLES` in `build_fixtures.py`.
- `csv-positive-control.csv` holds the same kind of values without the page's
  protection, to show that each application would evaluate them.

Applications: Microsoft Excel for Mac 16.114.4 and LibreOffice 26.8.1.1, macOS 26.3,
system locale `ja_JP`.

### Results

"Formulas" counts formula cells across every column of the sheet.

| Application | Path | Formulas | Titles as expected |
|---|---|---|---|
| Excel | Positive control | 4 of 4 `= + - @` values evaluated | n/a |
| Excel | Open CSV | 0 | 21 of 21 |
| Excel | … save as `.xlsx`, reopen | 0 | 21 of 21 |
| Excel | … save as CSV, reopen, save as CSV, reopen | 0 | 19 of 21 (see limitations) |
| LibreOffice | Positive control, "evaluate formulas" on | `=1+1` evaluated | n/a |
| LibreOffice | Import with "evaluate formulas" on | 0 | 21 of 21 |
| LibreOffice | Import with "evaluate formulas" off | 0 | 21 of 21 |
| LibreOffice | … save as `.xlsx`, reopen | 0 | 21 of 21 |
| LibreOffice | … save as CSV, reopen with evaluation on | 0 | 21 of 21 |

"As expected" means the cell holds the original text, with line breaks flattened, and
with the protective `'` when the value is risky. The `'` stays in the cell as a visible
character in both applications, and it survived every save and reopen above.

Excel also evaluates unprotected full-width `＝ ＋ －` when the file is read as UTF-8
(`＝1+1` gave 2, in a control file with no protective `'`), so the page's full-width handling is needed. Full-width `＠`, leading
ideographic and no-break spaces, and a leading tab were not evaluated even unprotected.

LibreOffice imports used comma separator, UTF-8, "detect special numbers" on and
"quoted field as text" off, through headless conversion.

### Limitations

- **Without the BOM** (the export before this change), Excel in this locale read the
  file as Shift-JIS and garbled non-ASCII text, so 7 of the 21 titles did not match.
  They still carried the `'` and none became a formula. Formula counts were also 0 after
  saving as `.xlsx` or CSV and reopening. Asking for UTF-8 through AppleScript's
  `open text file` (origin 65001) made no difference.
- **Programs reading the CSV** now see a BOM before the first header, `title`. Excel and
  LibreOffice both drop it, and the header cell stays `title`. Other readers may need
  to be told, for example Python's `utf-8-sig`.
- **Saving as CSV from Excel** writes the system encoding, so characters it cannot
  represent are lost. Titles beginning with a no-break space or BOM lost that character,
  which is the 19 of 21 above. They stayed text.
- **Not tested:** Excel for Windows, other locales, Excel's "CSV UTF-8" save format, the
  Data > From Text import wizard, Numbers, and Google Sheets.
- Excel was driven through AppleScript and LibreOffice headlessly. Nobody retyped or
  edited a cell by hand.
