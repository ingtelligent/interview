const analyzeBtn = document.getElementById('analyze-btn');
        const cvUpload = document.getElementById('cv-upload');
        const loading = document.getElementById('loading');
        const errorDiv = document.getElementById('error');
        const resultsDiv = document.getElementById('analysis-results');
        
        const API_BASE_URL = 'http://localhost:5000';

        analyzeBtn.addEventListener('click', async () => {
            const file = cvUpload.files[0];
            if (!file) {
                showError('Please upload a PDF file.');
                return;
            }

            if (file.type !== 'application/pdf') {
                showError('Only PDF files are supported.');
                return;
            }

            showLoading(true);
            clearError();
            resultsDiv.classList.add('hidden');

            try {
                const formData = new FormData();
                formData.append('pdf', file);

                const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
                    method: 'POST',
                    body: formData
                });

                if (!uploadResponse.ok) {
                    const errorData = await uploadResponse.json();
                    throw new Error(errorData.error || 'Failed to upload CV');
                }

                const { result_url } = await uploadResponse.json();
                const resultsResponse = await fetch(result_url);
                if (!resultsResponse.ok) {
                    const errorData = await resultsResponse.json();
                    throw new Error(errorData.error || 'Failed to fetch results');
                }

                const { raw } = await resultsResponse.json();
                renderAnalysis(raw);
                resultsDiv.classList.remove('hidden');
            } catch (error) {
                showError('Error analyzing CV: ' + error.message);
            } finally {
                showLoading(false);
            }
        });

        function renderAnalysis(analysis) {
            resultsDiv.innerHTML = '';
            if (analysis.error) {
                resultsDiv.innerHTML = `<p class="text-red-600">${analysis.error}</p>`;
                return;
            }

            const categories = [
                { key: 'thong_tin_ca_nhan', name: 'Thông Tin Cá Nhân' },
                { key: 'trinh_do_hoc_van', name: 'Trình Độ Học Vấn' },
                { key: 'kinh_nghiem_lam_viec', name: 'Kinh Nghiệm Làm Việc' },
                { key: 'ky_nang', name: 'Kỹ Năng' },
                { key: 'du_an_portfolio', name: 'Dự Án/Portfolio' },
                { key: 'cau_truc_va_dinh_dang', name: 'Cấu Trúc và Định Dạng' },
                { key: 'ngon_ngu_va_cach_dien_dat', name: 'Ngôn Ngữ và Cách Diễn Đạt' }
            ];

            categories.forEach(cat => {
                if (analysis[cat.key]) {
                    const data = analysis[cat.key];
                    const section = document.createElement('div');
                    section.className = 'mb-4 border rounded-lg';
                    section.innerHTML = `
                        <div class="accordion-header p-4 bg-gray-100 rounded-t-lg flex justify-between items-center">
                            <h2 class="text-lg font-semibold">${cat.name} (${data.diem}/10)</h2>
                            <svg class="w-5 h-5 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </div>
                        <div class="accordion-content p-4">
                            <h3 class="font-medium">Nhận xét chi tiết:</h3>
                            <p class="text-gray-600">${data.nhan_xet || 'Không có nhận xét.'}</p>
                            <h3 class="font-medium mt-4">Đề xuất cải thiện:</h3>
                            <p class="text-gray-600">${data.de_xuat || 'Không có đề xuất.'}</p>
                        </div>
                    `;
                    resultsDiv.appendChild(section);
                }
            });

            if (analysis.danh_gia_tong_the) {
                const total = analysis.danh_gia_tong_the;
                const section = document.createElement('div');
                section.className = 'mb-4 border rounded-lg';
                section.innerHTML = `
                    <div class="accordion-header p-4 bg-gray-100 rounded-t-lg flex justify-between items-center">
                        <h2 class="text-lg font-semibold">Đánh Giá Tổng Thể (${total.diem_trung_binh}/10)</h2>
                        <svg class="w-5 h-5 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </div>
                    <div class="accordion-content p-4">
                        <h3 class="font-medium">Phân tích tổng thể:</h3>
                        <p class="text-gray-600">${total.danh_gia_chi_tiet || 'Không có phân tích.'}</p>
                        <h3 class="font-medium mt-4">Điểm mạnh:</h3>
                        <ul class="list-disc pl-5 text-gray-600">${total.diem_manh.map(s => `<li>${s}</li>`).join('') || '<li>Không có điểm mạnh.</li>'}</ul>
                        <h3 class="font-medium mt-4">Điểm yếu:</h3>
                        <ul class="list-disc pl-5 text-gray-600">${total.diem_yeu.map(w => `<li>${w}</li>`).join('') || '<li>Không có điểm yếu.</li>'}</ul>
                        <h3 class="font-medium mt-4">Đề xuất cải thiện:</h3>
                        <ul class="list-disc pl-5 text-gray-600">${total.de_xuat_cai_thien.map(s => `<li>${s}</li>`).join('') || '<li>Không có đề xuất.</li>'}</ul>
                        <h3 class="font-medium mt-4">Nhận xét chung:</h3>
                        <p class="text-gray-600">${total.nhan_xet_chung || 'Không có nhận xét.'}</p>
                        <h3 class="font-medium mt-4">Tác động trên thị trường:</h3>
                        <p class="text-gray-600">${total.tac_dong_thi_truong || 'Không có phân tích.'}</p>
                    </div>
                `;
                resultsDiv.appendChild(section);
            }

            if (analysis.nganh_nghe_phu_hop && analysis.nganh_nghe_phu_hop.length > 0) {
                const section = document.createElement('div');
                section.className = 'mb-4 border rounded-lg';
                section.innerHTML = `
                    <div class="accordion-header p-4 bg-gray-100 rounded-t-lg flex justify-between items-center">
                        <h2 class="text-lg font-semibold">Ngành Nghề Phù Hợp</h2>
                        <svg class="w-5 h-5 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </div>
                    <div class="accordion-content p-4">
                        <ul class="list-disc pl-5 text-gray-600">${analysis.nganh_nghe_phu_hop.map(j => `<li>${j}</li>`).join('') || '<li>Không có ngành nghề phù hợp.</li>'}</ul>
                    </div>
                `;
                resultsDiv.appendChild(section);
            }

            if (analysis.phan_tich_xu_huong) {
                const section = document.createElement('div');
                section.className = 'mb-4 border rounded-lg';
                section.innerHTML = `
                    <div class="accordion-header p-4 bg-gray-100 rounded-t-lg flex justify-between items-center">
                        <h2 class="text-lg font-semibold">Phân Tích Xu Hướng Thị Trường</h2>
                        <svg class="w-5 h-5 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </div>
                    <div class="accordion-content p-4">
                        <p class="text-gray-600">${analysis.phan_tich_xu_huong || 'Không có phân tích.'}</p>
                    </div>
                `;
                resultsDiv.appendChild(section);
            }

            // Add accordion functionality
            document.querySelectorAll('.accordion-header').forEach(header => {
                header.addEventListener('click', () => {
                    const content = header.nextElementSibling;
                    const isOpen = content.classList.contains('show');
                    content.classList.toggle('show', !isOpen);
                    const svg = header.querySelector('svg');
                    svg.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
                });
            });
        }

        function showLoading(isLoading) {
            loading.style.display = isLoading ? 'block' : 'none';
            analyzeBtn.disabled = isLoading;
        }

        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }

        function clearError() {
            errorDiv.textContent = '';
            errorDiv.classList.add('hidden');
        }