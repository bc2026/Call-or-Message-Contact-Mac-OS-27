import Contacts
import Foundation

let store = CNContactStore()
let keys: [CNKeyDescriptor] = [
    CNContactFormatter.descriptorForRequiredKeys(for: .fullName),
    CNContactPhoneNumbersKey as CNKeyDescriptor
]
var results = [String]()
let request = CNContactFetchRequest(keysToFetch: keys)
do {
    try store.enumerateContacts(with: request) { contact, _ in
        let name = CNContactFormatter.string(from: contact, style: .fullName) ?? ""
        for phone in contact.phoneNumbers {
            let label = phone.label.flatMap { CNLabeledValue<NSString>.localizedString(forLabel: $0) } ?? ""
            results.append("\(name)\t\(phone.value.stringValue)\t\(label)")
        }
    }
} catch {
    fputs("Error: \(error)\n", stderr)
}
print(results.joined(separator: "\n"))
