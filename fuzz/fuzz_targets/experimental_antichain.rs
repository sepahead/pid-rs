#![no_main]

use libfuzzer_sys::fuzz_target;
use pid_core::experimental::continuous::Antichain3;

fuzz_target!(|data: &[u8]| {
    let count = data.first().map_or(0, |byte| usize::from(*byte % 5));
    let sets: Vec<u8> = data
        .iter()
        .skip(1)
        .take(count)
        .map(|byte| byte & 0b111)
        .collect();
    if let Ok(antichain) = Antichain3::try_from_sets(&sets) {
        let encoded = serde_json::to_vec(antichain.sets());
        if let Ok(encoded) = encoded {
            if let Ok(decoded) = serde_json::from_slice::<Vec<u8>>(&encoded) {
                let _ = Antichain3::try_from_sets(&decoded);
            }
        }
    }
});
