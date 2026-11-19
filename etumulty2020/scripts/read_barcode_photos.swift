// Read barcode images using the macOS Vision framework.
import Foundation
import Vision
import ImageIO

let paths = Array(CommandLine.arguments.dropFirst())
for path in paths {
    let url = URL(fileURLWithPath: path)
    var output: [String: Any] = ["file": url.lastPathComponent]
    do {
        let request = VNDetectBarcodesRequest()
        var codes = Set<String>()
        for orientation: CGImagePropertyOrientation in [.up, .right, .down, .left] {
            let handler = VNImageRequestHandler(url: url, orientation: orientation, options: [:])
            try handler.perform([request])
            codes.formUnion((request.results ?? []).compactMap { $0.payloadStringValue })
            if !codes.isEmpty { break }
        }
        output["barcodes"] = codes.sorted()
    } catch {
        output["barcodes"] = [String]()
        output["error"] = error.localizedDescription
    }
    let data = try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
    print(String(decoding: data, as: UTF8.self))
}
